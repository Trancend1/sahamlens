import { HermesStatus } from "@/components/HermesStatus";

export default function HermesPage() {
  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted">
        Monitor and control the Hermes agentic runtime. Hermes provides Telegram-based
        research and journaling capabilities.
      </p>
      <HermesStatus />
    </div>
  );
}
