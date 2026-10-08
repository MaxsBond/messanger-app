#include "Modules/ModuleManager.h"
#include "Misc/CoreDelegates.h"
#include "ToolsetRegistry/UToolsetRegistry.h"
#include "UMGAnimToolset.h"

class FUMGAnimToolsetModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		FCoreDelegates::OnAllModuleLoadingPhasesComplete.AddRaw(this, &FUMGAnimToolsetModule::Register);
		FCoreDelegates::OnPreExit.AddRaw(this, &FUMGAnimToolsetModule::Unregister);
	}
	virtual void ShutdownModule() override
	{
		FCoreDelegates::OnAllModuleLoadingPhasesComplete.RemoveAll(this);
		FCoreDelegates::OnPreExit.RemoveAll(this);
	}
private:
	void Register() { UToolsetRegistry::RegisterToolsetClass(UUMGAnimToolset::StaticClass()); }
	void Unregister() { UToolsetRegistry::UnregisterToolsetClass(UUMGAnimToolset::StaticClass()); }
};

IMPLEMENT_MODULE(FUMGAnimToolsetModule, UMGAnimToolset)
