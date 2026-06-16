import { LlmConfigForm } from "@/components/LlmConfigForm";
import { AppConfigForm } from "@/components/AppConfigForm";

export default function ConfigPage() {
  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted">
        Configure application settings. Changes are saved to .env.local and take effect on the next operation.
      </p>
      <LlmConfigForm />
      <AppConfigForm />
    </div>
  );
}
