using UnrealBuildTool;

public class UMGAnimToolset : ModuleRules
{
	public UMGAnimToolset(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "ToolsetRegistry", "UMG" });
		PrivateDependencyModuleNames.AddRange(new string[] {
			"UnrealEd", "UMGEditor", "Kismet", "Slate", "SlateCore", "MovieScene", "MovieSceneTracks" });
	}
}
