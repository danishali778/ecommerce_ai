import * as React from "react";
import clsx from "clsx";

export function cn(...values: Array<string | false | null | undefined>) {
  return clsx(values);
}

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", ...props },
  ref
) {
  const variants: Record<NonNullable<ButtonProps["variant"]>, string> = {
    primary: "bg-accent-500 text-white hover:bg-accent-600",
    secondary: "border border-slate-300 bg-white text-slate-900 hover:bg-slate-50",
    ghost: "bg-transparent text-slate-700 hover:bg-slate-100",
    danger: "bg-rose-600 text-white hover:bg-rose-700"
  };
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  );
});

export const Card = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("rounded-2xl border border-slate-200 bg-white shadow-sm", className)} {...props} />
);

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-accent-500 focus:ring-2 focus:ring-accent-100",
          className
        )}
        {...props}
      />
    );
  }
);

export function PasswordInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const [visible, setVisible] = React.useState(false);
  return (
    <div className="relative">
      <Input {...props} type={visible ? "text" : "password"} className={cn("pr-12", props.className)} />
      <button
        type="button"
        className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500"
        onClick={() => setVisible((value) => !value)}
      >
        {visible ? "Hide" : "Show"}
      </button>
    </div>
  );
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, ...props }, ref) {
    return (
      <textarea
        ref={ref}
        className={cn(
          "min-h-28 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-accent-500 focus:ring-2 focus:ring-accent-100",
          className
        )}
        {...props}
      />
    );
  }
);

export const Select = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, ...props }, ref) {
    return (
      <select
        ref={ref}
        className={cn(
          "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-accent-500 focus:ring-2 focus:ring-accent-100",
          className
        )}
        {...props}
      />
    );
  }
);

export const Checkbox = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  function Checkbox({ className, ...props }, ref) {
    return <input ref={ref} type="checkbox" className={cn("h-4 w-4 rounded border-slate-300 text-accent-500", className)} {...props} />;
  }
);

export function Badge({
  children,
  className,
  tone = "neutral"
}: React.PropsWithChildren<{ className?: string; tone?: "neutral" | "info" | "success" | "warning" | "danger" }>) {
  const tones = {
    neutral: "bg-slate-100 text-slate-700",
    info: "bg-blue-50 text-blue-700",
    success: "bg-emerald-50 text-emerald-700",
    warning: "bg-amber-50 text-amber-700",
    danger: "bg-rose-50 text-rose-700"
  };
  return <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-medium", tones[tone], className)}>{children}</span>;
}

export function Tabs({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-wrap gap-2", className)} {...props} />;
}

export function TabButton({
  active,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { active?: boolean }) {
  return (
    <button
      className={cn(
        "rounded-full px-3 py-1.5 text-sm transition",
        active ? "bg-accent-500 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200",
        className
      )}
      {...props}
    />
  );
}

export function Modal({
  open,
  onClose,
  children
}: React.PropsWithChildren<{ open: boolean; onClose: () => void }>) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4" onClick={onClose}>
      <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-soft" onClick={(event) => event.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

export function Drawer({
  open,
  onClose,
  children
}: React.PropsWithChildren<{ open: boolean; onClose: () => void }>) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-slate-950/40" onClick={onClose}>
      <div className="ml-auto h-full w-full max-w-xl overflow-y-auto bg-white p-6 shadow-soft" onClick={(event) => event.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
  return (
    <span className={cn("inline-flex h-9 w-9 items-center justify-center rounded-full bg-accent-50 text-sm font-semibold text-accent-700", className)}>
      {initials || "?"}
    </span>
  );
}

export function Tooltip({ content, children }: React.PropsWithChildren<{ content: string }>) {
  return (
    <span title={content} className="inline-flex">
      {children}
    </span>
  );
}

export function ProgressBar({ value }: { value: number }) {
  const safe = Math.max(0, Math.min(100, value));
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div className="h-full rounded-full bg-accent-500 transition-all" style={{ width: `${safe}%` }} />
    </div>
  );
}
