#include "UMGAnimToolset.h"

#include "Animation/MovieScene2DTransformSection.h"
#include "Animation/MovieScene2DTransformTrack.h"
#include "Animation/MovieSceneMarginSection.h"
#include "Animation/MovieSceneMarginTrack.h"
#include "Animation/WidgetAnimation.h"
#include "Blueprint/WidgetTree.h"
#include "Components/PanelSlot.h"
#include "Components/Widget.h"
#include "Editor.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "MovieScene.h"
#include "Sections/MovieSceneDoubleSection.h"
#include "Sections/MovieSceneFloatSection.h"
#include "Subsystems/AssetEditorSubsystem.h"
#include "Tracks/MovieSceneDoubleTrack.h"
#include "Tracks/MovieSceneFloatTrack.h"
#include "UObject/Package.h"
#include "WidgetBlueprint.h"
#include "WidgetBlueprintEditor.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(UMGAnimToolset)

namespace UMGAnim
{
	void Error(const FString& Msg)
	{
		UKismetSystemLibrary::RaiseScriptError(Msg);
	}

	UWidgetAnimation* FindAnimation(UWidgetBlueprint* BP, const FString& Name)
	{
		for (UWidgetAnimation* Anim : BP->Animations)
		{
			if (Anim && (Anim->GetName() == Name || Anim->GetDisplayLabel() == Name))
			{
				return Anim;
			}
		}
		return nullptr;
	}

	double TickRate(UMovieScene* MS) { return MS->GetTickResolution().AsDecimal(); }

	FFrameNumber ToFrame(UMovieScene* MS, double Seconds)
	{
		return FFrameNumber(static_cast<int32>(FMath::RoundToDouble(Seconds * TickRate(MS))));
	}

	double ToSeconds(UMovieScene* MS, FFrameNumber Frame) { return Frame.Value / TickRate(MS); }

	float Duration(UMovieScene* MS)
	{
		const TRange<FFrameNumber> R = MS->GetPlaybackRange();
		return static_cast<float>(ToSeconds(MS, R.GetUpperBoundValue() - R.GetLowerBoundValue()));
	}

	void SetDuration(UMovieScene* MS, double Seconds)
	{
		MS->SetPlaybackRange(FFrameNumber(0), ToFrame(MS, Seconds).Value);
		FMovieSceneEditorData& Ed = MS->GetEditorData();
		Ed.WorkStart = 0.0;
		Ed.WorkEnd = Seconds;
		Ed.ViewStart = -0.1;
		Ed.ViewEnd = Seconds + 0.1;
	}

	/** Refreshes the animation list of an open widget blueprint editor. */
	void NotifyEditor(UWidgetBlueprint* BP)
	{
		if (!GEditor)
		{
			return;
		}
		UAssetEditorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
		IAssetEditorInstance* Instance = Subsystem ? Subsystem->FindEditorForAsset(BP, false) : nullptr;
		if (Instance && Instance->GetEditorName() == FName("WidgetBlueprintEditor"))
		{
			static_cast<FWidgetBlueprintEditor*>(Instance)->NotifyWidgetAnimListChanged();
		}
	}

	// ---------- property spec ----------

	enum class EKind : uint8 { Transform, Margin, Scalar };

	struct FSpec
	{
		EKind Kind = EKind::Scalar;
		bool bSlot = false;            // property lives on the widget's panel slot
		FName PropertyName;            // RenderTransform / Padding / RenderOpacity ...
		int32 Channel = 0;             // Transform: 0 TX,1 TY,2 Angle,3 SX,4 SY,5 ShX,6 ShY; Margin: 0 L,1 T,2 R,3 B
		bool bDouble = false;          // scalar double property
	};

	bool ParseSpec(UWidget* Widget, const FString& InProperty, FSpec& Out, FString& Err)
	{
		FString P = InProperty.TrimStartAndEnd();
		if (P.StartsWith(TEXT("RenderTransform.")))
		{
			P.RightChopInline(16);
		}

		static const TMap<FString, int32> TransformChannels = {
			{TEXT("Translation.X"), 0}, {TEXT("Translation.Y"), 1}, {TEXT("Angle"), 2}, {TEXT("Rotation"), 2},
			{TEXT("Scale.X"), 3}, {TEXT("Scale.Y"), 4}, {TEXT("Shear.X"), 5}, {TEXT("Shear.Y"), 6}};
		if (const int32* Idx = TransformChannels.Find(P))
		{
			Out.Kind = EKind::Transform;
			Out.PropertyName = TEXT("RenderTransform");
			Out.Channel = *Idx;
			return true;
		}

		UObject* Owner = Widget;
		if (P.StartsWith(TEXT("Slot.")))
		{
			if (!Widget->Slot)
			{
				Err = FString::Printf(TEXT("Widget '%s' has no panel slot."), *Widget->GetName());
				return false;
			}
			Out.bSlot = true;
			Owner = Widget->Slot;
			P.RightChopInline(5);
		}

		FString Left, Side;
		if (P.Split(TEXT("."), &Left, &Side))
		{
			static const TMap<FString, int32> Sides = {{TEXT("Left"), 0}, {TEXT("Top"), 1}, {TEXT("Right"), 2}, {TEXT("Bottom"), 3}};
			const FStructProperty* SP = FindFProperty<FStructProperty>(Owner->GetClass(), *Left);
			const int32* SideIdx = Sides.Find(Side);
			if (!SP || SP->Struct != TBaseStructure<FMargin>::Get() || !SideIdx)
			{
				Err = FString::Printf(TEXT("'%s' is not an FMargin channel on %s (use <MarginProperty>.Left/Top/Right/Bottom)."), *InProperty, *Owner->GetClass()->GetName());
				return false;
			}
			Out.Kind = EKind::Margin;
			Out.PropertyName = SP->GetFName();
			Out.Channel = *SideIdx;
			return true;
		}

		if (Out.bSlot)
		{
			Err = TEXT("Only FMargin channels (e.g. Slot.Padding.Left) are supported on slots.");
			return false;
		}
		const FProperty* Prop = FindFProperty<FProperty>(Owner->GetClass(), *P);
		if (Prop && (Prop->IsA<FFloatProperty>() || Prop->IsA<FDoubleProperty>()))
		{
			Out.Kind = EKind::Scalar;
			Out.PropertyName = Prop->GetFName();
			Out.bDouble = Prop->IsA<FDoubleProperty>();
			return true;
		}
		Err = FString::Printf(TEXT("Unsupported property '%s' on %s. Use Translation.X/Y, Scale.X/Y, Angle, Shear.X/Y, "
			"Slot.Padding.Left/Top/Right/Bottom, <Margin>.<Side>, or a float/double property name."), *InProperty, *Owner->GetClass()->GetName());
		return false;
	}

	// ---------- bindings ----------

	FGuid FindBinding(UWidgetAnimation* Anim, UWidget* Widget, bool bSlot)
	{
		for (const FWidgetAnimationBinding& B : Anim->AnimationBindings)
		{
			if (B.bIsRootWidget || B.WidgetName != Widget->GetFName())
			{
				continue;
			}
			if (bSlot ? (Widget->Slot && B.SlotWidgetName == Widget->Slot->GetFName()) : B.SlotWidgetName.IsNone())
			{
				return B.AnimationGuid;
			}
		}
		return FGuid();
	}

	FGuid GetOrCreateBinding(UWidgetAnimation* Anim, UWidget* Widget, bool bSlot)
	{
		FGuid Guid = FindBinding(Anim, Widget, bSlot);
		if (Guid.IsValid())
		{
			return Guid;
		}
		UMovieScene* MS = Anim->GetMovieScene();
		if (!bSlot)
		{
			Guid = MS->AddPossessable(Widget->GetName(), Widget->GetClass());
			FWidgetAnimationBinding B;
			B.AnimationGuid = Guid;
			B.WidgetName = Widget->GetFName();
			B.bIsRootWidget = false;
			Anim->AnimationBindings.Add(B);
			return Guid;
		}
		const FGuid ParentGuid = GetOrCreateBinding(Anim, Widget, false);
		Guid = MS->AddPossessable(Widget->Slot->GetName(), Widget->Slot->GetClass());
		if (FMovieScenePossessable* Possessable = MS->FindPossessable(Guid))
		{
			Possessable->SetParent(ParentGuid, MS);
		}
		FWidgetAnimationBinding B;
		B.AnimationGuid = Guid;
		B.WidgetName = Widget->GetFName();
		B.SlotWidgetName = Widget->Slot->GetFName();
		B.bIsRootWidget = false;
		Anim->AnimationBindings.Add(B);
		return Guid;
	}

	UMovieScenePropertyTrack* FindTrack(UMovieScene* MS, const FGuid& Guid, FName PropertyName)
	{
		if (const FMovieSceneBinding* Binding = MS->FindBinding(Guid))
		{
			for (UMovieSceneTrack* Track : Binding->GetTracks())
			{
				UMovieScenePropertyTrack* PT = Cast<UMovieScenePropertyTrack>(Track);
				if (PT && PT->GetPropertyName() == PropertyName)
				{
					return PT;
				}
			}
		}
		return nullptr;
	}

	UMovieSceneSection* GetOrCreateSection(UWidgetAnimation* Anim, UWidget* Widget, const FSpec& Spec)
	{
		UMovieScene* MS = Anim->GetMovieScene();
		const FGuid Guid = GetOrCreateBinding(Anim, Widget, Spec.bSlot);
		UMovieScenePropertyTrack* Track = FindTrack(MS, Guid, Spec.PropertyName);
		if (!Track)
		{
			TSubclassOf<UMovieSceneTrack> TrackClass =
				Spec.Kind == EKind::Transform ? UMovieScene2DTransformTrack::StaticClass()
				: Spec.Kind == EKind::Margin ? UMovieSceneMarginTrack::StaticClass()
				: Spec.bDouble ? UMovieSceneDoubleTrack::StaticClass()
				: UMovieSceneFloatTrack::StaticClass();
			Track = Cast<UMovieScenePropertyTrack>(MS->AddTrack(TrackClass, Guid));
			Track->SetPropertyNameAndPath(Spec.PropertyName, Spec.PropertyName.ToString());
		}
		if (Track->GetAllSections().Num() > 0)
		{
			return Track->GetAllSections()[0];
		}

		UMovieSceneSection* Section = Track->CreateNewSection();
		Section->SetRange(TRange<FFrameNumber>::All());
		Section->EvalOptions.CompletionMode = EMovieSceneCompletionMode::KeepState;

		// Channels without keys evaluate to their default: seed defaults from the widget's current values.
		if (UMovieScene2DTransformSection* TS = Cast<UMovieScene2DTransformSection>(Section))
		{
			const FWidgetTransform& T = Widget->GetRenderTransform();
			TS->Translation[0].SetDefault(T.Translation.X);
			TS->Translation[1].SetDefault(T.Translation.Y);
			TS->Rotation.SetDefault(T.Angle);
			TS->Scale[0].SetDefault(T.Scale.X);
			TS->Scale[1].SetDefault(T.Scale.Y);
			TS->Shear[0].SetDefault(T.Shear.X);
			TS->Shear[1].SetDefault(T.Shear.Y);
		}
		else if (UMovieSceneMarginSection* MSec = Cast<UMovieSceneMarginSection>(Section))
		{
			UObject* Owner = Spec.bSlot ? static_cast<UObject*>(Widget->Slot) : Widget;
			if (const FStructProperty* SP = FindFProperty<FStructProperty>(Owner->GetClass(), Spec.PropertyName))
			{
				const FMargin* M = SP->ContainerPtrToValuePtr<FMargin>(Owner);
				MSec->LeftCurve.SetDefault(M->Left);
				MSec->TopCurve.SetDefault(M->Top);
				MSec->RightCurve.SetDefault(M->Right);
				MSec->BottomCurve.SetDefault(M->Bottom);
			}
		}
		Track->AddSection(*Section);
		return Section;
	}

	// ---------- keys ----------

	template <typename ChannelT, typename ValueT>
	void WriteKeys(UMovieScene* MS, ChannelT& Channel, TArray<FUMGAnimKey> Keys)
	{
		Keys.Sort([](const FUMGAnimKey& A, const FUMGAnimKey& B) { return A.Time < B.Time; });
		const double Rate = TickRate(MS);
		Channel.GetData().Reset();

		bool bAuto = false;
		TArray<ValueT> Values;
		Values.SetNum(Keys.Num());
		for (int32 i = 0; i < Keys.Num(); ++i)
		{
			ValueT& V = Values[i];
			V.Value = Keys[i].Value;
			V.InterpMode = RCIM_Cubic;
			V.TangentMode = RCTM_Break;
			V.Tangent.TangentWeightMode = RCTWM_WeightedNone;
			V.Tangent.ArriveTangent = 0.f;
			V.Tangent.LeaveTangent = 0.f;
		}
		for (int32 i = 0; i < Keys.Num(); ++i)
		{
			const FString Ease = Keys[i].Ease.ToLower();
			ValueT& V = Values[i];
			if (i + 1 >= Keys.Num())
			{
				break;
			}
			const double Dt = FMath::Max(Keys[i + 1].Time - Keys[i].Time, 1e-4f) * Rate;
			const float Slope = static_cast<float>((Keys[i + 1].Value - Keys[i].Value) / Dt);
			ValueT& Next = Values[i + 1];
			if (Ease == TEXT("linear"))
			{
				V.InterpMode = RCIM_Linear;
				V.Tangent.LeaveTangent = Slope;
				Next.Tangent.ArriveTangent = Slope;
			}
			else if (Ease == TEXT("constant") || Ease == TEXT("step"))
			{
				V.InterpMode = RCIM_Constant;
			}
			else if (Ease == TEXT("easeout") || Ease == TEXT("ease-out"))
			{
				V.Tangent.LeaveTangent = 2.f * Slope;
			}
			else if (Ease == TEXT("easein") || Ease == TEXT("ease-in"))
			{
				Next.Tangent.ArriveTangent = 2.f * Slope;
			}
			else if (Ease == TEXT("auto") || Ease == TEXT("smooth"))
			{
				V.TangentMode = RCTM_Auto;
				Next.TangentMode = RCTM_Auto;
				bAuto = true;
			}
			// easeInOut / anything else: flat tangents on both ends
		}
		for (int32 i = 0; i < Keys.Num(); ++i)
		{
			Channel.GetData().AddKey(ToFrame(MS, Keys[i].Time), Values[i]);
		}
		if (Keys.Num() > 0)
		{
			Channel.SetDefault(Keys[0].Value);
		}
		if (bAuto)
		{
			Channel.AutoSetTangents();
		}
	}

	FString DescribeChannel(UMovieScene* MS, const FMovieSceneFloatChannel& C)
	{
		FString S;
		TArrayView<const FFrameNumber> Times = C.GetData().GetTimes();
		TArrayView<const FMovieSceneFloatValue> Vals = C.GetData().GetValues();
		for (int32 i = 0; i < Times.Num(); ++i)
		{
			S += FString::Printf(TEXT(" %.3g=%.4g"), ToSeconds(MS, Times[i]), Vals[i].Value);
		}
		return S;
	}

	FString DescribeChannel(UMovieScene* MS, const FMovieSceneDoubleChannel& C)
	{
		FString S;
		TArrayView<const FFrameNumber> Times = C.GetData().GetTimes();
		TArrayView<const FMovieSceneDoubleValue> Vals = C.GetData().GetValues();
		for (int32 i = 0; i < Times.Num(); ++i)
		{
			S += FString::Printf(TEXT(" %.3g=%.4g"), ToSeconds(MS, Times[i]), Vals[i].Value);
		}
		return S;
	}

	FUMGAnimInfo Describe(UWidgetAnimation* Anim)
	{
		FUMGAnimInfo Info;
		if (!Anim)
		{
			return Info;
		}
		UMovieScene* MS = Anim->GetMovieScene();
		Info.Name = Anim->GetName();
		Info.Duration = Duration(MS);
		for (const FWidgetAnimationBinding& B : Anim->AnimationBindings)
		{
			const FMovieSceneBinding* Binding = MS->FindBinding(B.AnimationGuid);
			if (!Binding)
			{
				continue;
			}
			const FString Target = B.bIsRootWidget ? TEXT("<root>")
				: B.SlotWidgetName.IsNone() ? B.WidgetName.ToString()
				: B.WidgetName.ToString() + TEXT(".Slot");
			for (UMovieSceneTrack* Track : Binding->GetTracks())
			{
				for (UMovieSceneSection* Section : Track->GetAllSections())
				{
					auto Add = [&](const TCHAR* Name, const FString& Keys)
					{
						if (!Keys.IsEmpty())
						{
							Info.Channels.Add(FString::Printf(TEXT("%s:%s%s"), *Target, Name, *Keys));
						}
					};
					if (UMovieScene2DTransformSection* TS = Cast<UMovieScene2DTransformSection>(Section))
					{
						Add(TEXT("Translation.X"), DescribeChannel(MS, TS->Translation[0]));
						Add(TEXT("Translation.Y"), DescribeChannel(MS, TS->Translation[1]));
						Add(TEXT("Angle"), DescribeChannel(MS, TS->Rotation));
						Add(TEXT("Scale.X"), DescribeChannel(MS, TS->Scale[0]));
						Add(TEXT("Scale.Y"), DescribeChannel(MS, TS->Scale[1]));
						Add(TEXT("Shear.X"), DescribeChannel(MS, TS->Shear[0]));
						Add(TEXT("Shear.Y"), DescribeChannel(MS, TS->Shear[1]));
					}
					else if (UMovieSceneMarginSection* MSec = Cast<UMovieSceneMarginSection>(Section))
					{
						const FString P = Cast<UMovieScenePropertyTrack>(Track)->GetPropertyName().ToString();
						Add(*(P + TEXT(".Left")), DescribeChannel(MS, MSec->LeftCurve));
						Add(*(P + TEXT(".Top")), DescribeChannel(MS, MSec->TopCurve));
						Add(*(P + TEXT(".Right")), DescribeChannel(MS, MSec->RightCurve));
						Add(*(P + TEXT(".Bottom")), DescribeChannel(MS, MSec->BottomCurve));
					}
					else if (UMovieSceneFloatSection* FS = Cast<UMovieSceneFloatSection>(Section))
					{
						Add(*Cast<UMovieScenePropertyTrack>(Track)->GetPropertyName().ToString(), DescribeChannel(MS, FS->GetChannel()));
					}
					else if (UMovieSceneDoubleSection* DS = Cast<UMovieSceneDoubleSection>(Section))
					{
						Add(*Cast<UMovieScenePropertyTrack>(Track)->GetPropertyName().ToString(), DescribeChannel(MS, DS->GetChannel()));
					}
				}
			}
		}
		return Info;
	}

	void ClearAll(UWidgetAnimation* Anim)
	{
		UMovieScene* MS = Anim->GetMovieScene();
		for (const FWidgetAnimationBinding& B : TArray<FWidgetAnimationBinding>(Anim->AnimationBindings))
		{
			MS->RemovePossessable(B.AnimationGuid);
		}
		Anim->AnimationBindings.Reset();
	}

	bool ResolveAnimWidget(UWidgetBlueprint* BP, const FString& AnimationName, const FString& WidgetName,
		UWidgetAnimation*& OutAnim, UWidget*& OutWidget, const TCHAR* Tool)
	{
		if (!BP)
		{
			Error(FString::Printf(TEXT("%s: WidgetBlueprint is required."), Tool));
			return false;
		}
		OutAnim = FindAnimation(BP, AnimationName);
		if (!OutAnim)
		{
			Error(FString::Printf(TEXT("%s: no animation '%s' in %s."), Tool, *AnimationName, *BP->GetName()));
			return false;
		}
		OutWidget = BP->WidgetTree ? BP->WidgetTree->FindWidget(FName(*WidgetName)) : nullptr;
		if (!OutWidget)
		{
			Error(FString::Printf(TEXT("%s: no widget '%s' in %s."), Tool, *WidgetName, *BP->GetName()));
			return false;
		}
		return true;
	}
}

TArray<FUMGAnimInfo> UUMGAnimToolset::ListAnimations(UWidgetBlueprint* WidgetBlueprint)
{
	TArray<FUMGAnimInfo> Out;
	if (!WidgetBlueprint)
	{
		UMGAnim::Error(TEXT("ListAnimations: WidgetBlueprint is required."));
		return Out;
	}
	for (UWidgetAnimation* Anim : WidgetBlueprint->Animations)
	{
		if (Anim && Anim->GetMovieScene())
		{
			Out.Add(UMGAnim::Describe(Anim));
		}
	}
	return Out;
}

FUMGAnimInfo UUMGAnimToolset::CreateAnimation(UWidgetBlueprint* WidgetBlueprint, const FString& Name, float Duration, bool bReplaceExisting)
{
	if (!WidgetBlueprint || Name.IsEmpty() || Duration <= 0.f)
	{
		UMGAnim::Error(TEXT("CreateAnimation: WidgetBlueprint, Name and a positive Duration are required."));
		return FUMGAnimInfo();
	}
	if (UWidgetAnimation* Existing = UMGAnim::FindAnimation(WidgetBlueprint, Name))
	{
		if (!bReplaceExisting)
		{
			UMGAnim::Error(FString::Printf(TEXT("CreateAnimation: '%s' already exists (pass bReplaceExisting=true to clear it)."), *Name));
			return FUMGAnimInfo();
		}
		Existing->Modify();
		Existing->GetMovieScene()->Modify();
		UMGAnim::ClearAll(Existing);
		UMGAnim::SetDuration(Existing->GetMovieScene(), Duration);
		FBlueprintEditorUtils::MarkBlueprintAsModified(WidgetBlueprint);
		UMGAnim::NotifyEditor(WidgetBlueprint);
		return UMGAnim::Describe(Existing);
	}
	const FName NewName(*Name);
	if ((WidgetBlueprint->WidgetTree && WidgetBlueprint->WidgetTree->FindWidget(NewName))
		|| FBlueprintEditorUtils::FindNewVariableIndex(WidgetBlueprint, NewName) != INDEX_NONE
		|| StaticFindObject(nullptr, WidgetBlueprint, *Name) != nullptr)
	{
		UMGAnim::Error(FString::Printf(TEXT("CreateAnimation: name '%s' is already used in %s."), *Name, *WidgetBlueprint->GetName()));
		return FUMGAnimInfo();
	}

	WidgetBlueprint->Modify();
	UWidgetAnimation* Anim = NewObject<UWidgetAnimation>(WidgetBlueprint, NewName, RF_Transactional);
	Anim->SetDisplayLabel(Name);
	Anim->MovieScene = NewObject<UMovieScene>(Anim, NewName, RF_Transactional);
	Anim->MovieScene->SetDisplayRate(FFrameRate(60, 1));
	UMGAnim::SetDuration(Anim->MovieScene, Duration);

	WidgetBlueprint->Animations.Add(Anim);
	WidgetBlueprint->OnVariableAdded(Anim->GetFName());
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WidgetBlueprint);
	UMGAnim::NotifyEditor(WidgetBlueprint);
	return UMGAnim::Describe(Anim);
}

bool UUMGAnimToolset::DeleteAnimation(UWidgetBlueprint* WidgetBlueprint, const FString& Name)
{
	UWidgetAnimation* Anim = WidgetBlueprint ? UMGAnim::FindAnimation(WidgetBlueprint, Name) : nullptr;
	if (!Anim)
	{
		UMGAnim::Error(FString::Printf(TEXT("DeleteAnimation: no animation '%s'."), *Name));
		return false;
	}
	WidgetBlueprint->Modify();
	WidgetBlueprint->Animations.Remove(Anim);
	// Free the name so an animation with the same name can be created again.
	Anim->Rename(nullptr, GetTransientPackage(), REN_DontCreateRedirectors | REN_NonTransactional);
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WidgetBlueprint);
	UMGAnim::NotifyEditor(WidgetBlueprint);
	return true;
}

bool UUMGAnimToolset::SetAnimationDuration(UWidgetBlueprint* WidgetBlueprint, const FString& Name, float Duration)
{
	UWidgetAnimation* Anim = WidgetBlueprint ? UMGAnim::FindAnimation(WidgetBlueprint, Name) : nullptr;
	if (!Anim || Duration <= 0.f)
	{
		UMGAnim::Error(FString::Printf(TEXT("SetAnimationDuration: no animation '%s' or non-positive duration."), *Name));
		return false;
	}
	Anim->GetMovieScene()->Modify();
	UMGAnim::SetDuration(Anim->GetMovieScene(), Duration);
	FBlueprintEditorUtils::MarkBlueprintAsModified(WidgetBlueprint);
	return true;
}

FUMGAnimInfo UUMGAnimToolset::SetKeys(UWidgetBlueprint* WidgetBlueprint, const FString& AnimationName, const FString& WidgetName,
	const FString& Property, const TArray<FUMGAnimKey>& Keys)
{
	UWidgetAnimation* Anim = nullptr;
	UWidget* Widget = nullptr;
	if (!UMGAnim::ResolveAnimWidget(WidgetBlueprint, AnimationName, WidgetName, Anim, Widget, TEXT("SetKeys")))
	{
		return FUMGAnimInfo();
	}
	if (Keys.Num() == 0)
	{
		UMGAnim::Error(TEXT("SetKeys: at least one key is required (use RemoveTrack to delete)."));
		return FUMGAnimInfo();
	}
	UMGAnim::FSpec Spec;
	FString Err;
	if (!UMGAnim::ParseSpec(Widget, Property, Spec, Err))
	{
		UMGAnim::Error(TEXT("SetKeys: ") + Err);
		return FUMGAnimInfo();
	}

	UMovieScene* MS = Anim->GetMovieScene();
	Anim->Modify();
	MS->Modify();
	UMovieSceneSection* Section = UMGAnim::GetOrCreateSection(Anim, Widget, Spec);
	Section->Modify();

	if (UMovieScene2DTransformSection* TS = Cast<UMovieScene2DTransformSection>(Section))
	{
		FMovieSceneFloatChannel* Channels[] = {&TS->Translation[0], &TS->Translation[1], &TS->Rotation,
			&TS->Scale[0], &TS->Scale[1], &TS->Shear[0], &TS->Shear[1]};
		UMGAnim::WriteKeys<FMovieSceneFloatChannel, FMovieSceneFloatValue>(MS, *Channels[Spec.Channel], Keys);
	}
	else if (UMovieSceneMarginSection* MSec = Cast<UMovieSceneMarginSection>(Section))
	{
		FMovieSceneFloatChannel* Channels[] = {&MSec->LeftCurve, &MSec->TopCurve, &MSec->RightCurve, &MSec->BottomCurve};
		UMGAnim::WriteKeys<FMovieSceneFloatChannel, FMovieSceneFloatValue>(MS, *Channels[Spec.Channel], Keys);
	}
	else if (UMovieSceneFloatSection* FS = Cast<UMovieSceneFloatSection>(Section))
	{
		UMGAnim::WriteKeys<FMovieSceneFloatChannel, FMovieSceneFloatValue>(MS, FS->GetChannel(), Keys);
	}
	else if (UMovieSceneDoubleSection* DS = Cast<UMovieSceneDoubleSection>(Section))
	{
		UMGAnim::WriteKeys<FMovieSceneDoubleChannel, FMovieSceneDoubleValue>(MS, DS->GetChannel(), Keys);
	}

	float LastTime = 0.f;
	for (const FUMGAnimKey& K : Keys)
	{
		LastTime = FMath::Max(LastTime, K.Time);
	}
	if (LastTime > UMGAnim::Duration(MS) + KINDA_SMALL_NUMBER)
	{
		UMGAnim::SetDuration(MS, LastTime);
	}

	FBlueprintEditorUtils::MarkBlueprintAsModified(WidgetBlueprint);
	UMGAnim::NotifyEditor(WidgetBlueprint);
	return UMGAnim::Describe(Anim);
}

FUMGAnimInfo UUMGAnimToolset::RemoveTrack(UWidgetBlueprint* WidgetBlueprint, const FString& AnimationName, const FString& WidgetName, const FString& Property)
{
	UWidgetAnimation* Anim = nullptr;
	UWidget* Widget = nullptr;
	if (!UMGAnim::ResolveAnimWidget(WidgetBlueprint, AnimationName, WidgetName, Anim, Widget, TEXT("RemoveTrack")))
	{
		return FUMGAnimInfo();
	}
	UMovieScene* MS = Anim->GetMovieScene();
	Anim->Modify();
	MS->Modify();

	if (Property.TrimStartAndEnd().IsEmpty())
	{
		for (bool bSlot : {true, false})
		{
			const FGuid Guid = UMGAnim::FindBinding(Anim, Widget, bSlot);
			if (Guid.IsValid())
			{
				MS->RemovePossessable(Guid);
				Anim->AnimationBindings.RemoveAll([&Guid](const FWidgetAnimationBinding& B) { return B.AnimationGuid == Guid; });
			}
		}
	}
	else
	{
		UMGAnim::FSpec Spec;
		FString Err;
		if (!UMGAnim::ParseSpec(Widget, Property, Spec, Err))
		{
			UMGAnim::Error(TEXT("RemoveTrack: ") + Err);
			return FUMGAnimInfo();
		}
		const FGuid Guid = UMGAnim::FindBinding(Anim, Widget, Spec.bSlot);
		if (UMovieScenePropertyTrack* Track = Guid.IsValid() ? UMGAnim::FindTrack(MS, Guid, Spec.PropertyName) : nullptr)
		{
			MS->RemoveTrack(*Track);
		}
	}
	FBlueprintEditorUtils::MarkBlueprintAsModified(WidgetBlueprint);
	UMGAnim::NotifyEditor(WidgetBlueprint);
	return UMGAnim::Describe(Anim);
}
