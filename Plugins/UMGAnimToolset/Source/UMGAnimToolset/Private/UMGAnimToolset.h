#pragma once

#include "CoreMinimal.h"
#include "ToolsetRegistry/ToolsetDefinition.h"
#include "UMGAnimToolset.generated.h"

class UWidgetBlueprint;

/** One key of an animated property. */
USTRUCT(BlueprintType)
struct FUMGAnimKey
{
	GENERATED_BODY()

	/** Key time in seconds from the start of the animation. */
	UPROPERTY(BlueprintReadWrite, Category = "UMGAnim")
	float Time = 0.f;

	/** Property value at this key (opacity 0..1, translation in slate units, scale factor, angle in degrees, ...). */
	UPROPERTY(BlueprintReadWrite, Category = "UMGAnim")
	float Value = 0.f;

	/**
	 * Curve from this key to the NEXT key:
	 *   "linear", "constant" (step), "easeIn" (accelerate), "easeOut" (decelerate),
	 *   "easeInOut" (default, flat tangents on both ends), "auto" (Sequencer auto tangents).
	 * Ignored on the last key.
	 */
	UPROPERTY(BlueprintReadWrite, Category = "UMGAnim")
	FString Ease = TEXT("easeInOut");
};

/** Summary of one animation in a widget blueprint. */
USTRUCT(BlueprintType)
struct FUMGAnimInfo
{
	GENERATED_BODY()

	/** Animation name, also the name of the blueprint variable (use with PlayAnimation). */
	UPROPERTY(BlueprintReadOnly, Category = "UMGAnim")
	FString Name;

	/** Playback length in seconds. */
	UPROPERTY(BlueprintReadOnly, Category = "UMGAnim")
	float Duration = 0.f;

	/** One line per animated channel: "Widget:Property  t=v(ease) t=v ...". */
	UPROPERTY(BlueprintReadOnly, Category = "UMGAnim")
	TArray<FString> Channels;
};

/**
 * Tools for authoring UMG widget animations (the Animations panel / Sequencer timeline of a Widget Blueprint).
 *
 * Typical flow:
 *   1. CreateAnimation(WBP, "Anim_Open", 0.6)
 *   2. SetKeys(WBP, "Anim_Open", "Panel", "RenderOpacity", [{time:0,value:0,ease:"easeOut"},{time:0.3,value:1}])
 *      SetKeys(WBP, "Anim_Open", "Panel", "Translation.X", [...])
 *   3. UMGToolSet.CompileWidgetBlueprint(WBP), then play it from Blueprint: PlayAnimation(Anim_Open).
 *
 * Supported Property values for SetKeys / RemoveTrack:
 *   - "Translation.X" / "Translation.Y" / "Scale.X" / "Scale.Y" / "Angle" / "Shear.X" / "Shear.Y"
 *       -> channels of the widget RenderTransform (pivot = RenderTransformPivot, set it on the widget).
 *   - "Slot.Padding.Left" / ".Top" / ".Right" / ".Bottom"  -> the widget's panel slot padding.
 *   - "<Name>.Left/Top/Right/Bottom" for any FMargin property of the widget (e.g. "Padding.Left" on a Border).
 *   - any float or double property of the widget by name: "RenderOpacity", "WidthOverride", "HeightOverride", ...
 * Widgets are addressed by their name in the widget tree. Keys replace the existing keys of that channel.
 */
UCLASS(BlueprintType)
class UUMGAnimToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Lists the widget animations of a widget blueprint with their animated channels and keys.
	 * @param WidgetBlueprint The widget blueprint to inspect.
	 */
	UFUNCTION(meta = (AICallable), Category = "UMGAnim")
	static TArray<FUMGAnimInfo> ListAnimations(UWidgetBlueprint* WidgetBlueprint);

	/**
	 * Creates a new widget animation. Fails if one with this name exists unless bReplaceExisting is true
	 * (then all its tracks are cleared and the duration is reset).
	 * @param WidgetBlueprint The widget blueprint.
	 * @param Name Animation name (a valid blueprint variable name, e.g. "Anim_OpenMenu").
	 * @param Duration Playback length in seconds.
	 * @param bReplaceExisting Clear and reuse an existing animation with this name.
	 */
	UFUNCTION(meta = (AICallable), Category = "UMGAnim")
	static FUMGAnimInfo CreateAnimation(UWidgetBlueprint* WidgetBlueprint, const FString& Name, float Duration, bool bReplaceExisting = false);

	/**
	 * Deletes a widget animation.
	 * @param WidgetBlueprint The widget blueprint.
	 * @param Name Animation name.
	 */
	UFUNCTION(meta = (AICallable), Category = "UMGAnim")
	static bool DeleteAnimation(UWidgetBlueprint* WidgetBlueprint, const FString& Name);

	/**
	 * Sets the playback length of an animation.
	 * @param WidgetBlueprint The widget blueprint.
	 * @param Name Animation name.
	 * @param Duration New length in seconds.
	 */
	UFUNCTION(meta = (AICallable), Category = "UMGAnim")
	static bool SetAnimationDuration(UWidgetBlueprint* WidgetBlueprint, const FString& Name, float Duration);

	/**
	 * Replaces the keys of one animated channel of a widget, creating the binding and track as needed.
	 * The animation length grows automatically to fit the last key.
	 * @param WidgetBlueprint The widget blueprint.
	 * @param AnimationName Animation name.
	 * @param WidgetName Widget name in the widget tree.
	 * @param Property Channel, see the toolset description (e.g. "RenderOpacity", "Translation.X", "Scale.Y", "Slot.Padding.Left", "WidthOverride").
	 * @param Keys Keys sorted or unsorted by time; Ease on a key shapes the curve towards the next key.
	 */
	UFUNCTION(meta = (AICallable), Category = "UMGAnim")
	static FUMGAnimInfo SetKeys(UWidgetBlueprint* WidgetBlueprint, const FString& AnimationName, const FString& WidgetName, const FString& Property, const TArray<FUMGAnimKey>& Keys);

	/**
	 * Removes animation data for a widget. Empty Property removes the whole widget binding (and its slot binding);
	 * otherwise removes the track that holds that channel (for RenderTransform / padding this drops all their channels).
	 * @param WidgetBlueprint The widget blueprint.
	 * @param AnimationName Animation name.
	 * @param WidgetName Widget name in the widget tree.
	 * @param Property Channel or empty.
	 */
	UFUNCTION(meta = (AICallable), Category = "UMGAnim")
	static FUMGAnimInfo RemoveTrack(UWidgetBlueprint* WidgetBlueprint, const FString& AnimationName, const FString& WidgetName, const FString& Property);
};
