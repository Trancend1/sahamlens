interface DataTableWrapperProps {
  children: React.ReactNode;
}

export function DataTableWrapper({ children }: DataTableWrapperProps): React.ReactElement {
  return (
    <div className="overflow-x-auto rounded-md border border-muted/30 bg-white/[0.02]">
      {children}
    </div>
  );
}
