interface CommandBlockProps {
  command: string;
}

export function CommandBlock({ command }: CommandBlockProps): React.ReactElement {
  return (
    <pre className="mt-3 overflow-x-auto rounded-md border border-muted/20 bg-black/30 p-3 text-xs text-muted">
      <code className="font-mono">{command}</code>
    </pre>
  );
}
