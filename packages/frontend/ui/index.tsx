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
    primary:
      "border border-accent-600 bg-accent-600 text-white shadow-[0_10px_24px_rgba(37,99,235,0.18)] hover:bg-accent-700 hover:shadow-[0_14px_28px_rgba(37,99,235,0.22)] active:translate-y-0",
    secondary:
      "border border-slate-200 bg-white text-slate-800 shadow-[0_6px_18px_rgba(15,23,42,0.05)] hover:border-slate-300 hover:bg-slate-50 active:translate-y-0",
    ghost: "bg-transparent text-slate-600 hover:bg-slate-100/80 hover:text-slate-900",
    danger:
      "border border-rose-600 bg-rose-600 text-white shadow-[0_10px_24px_rgba(190,24,93,0.16)] hover:bg-rose-700 hover:shadow-[0_14px_28px_rgba(190,24,93,0.20)] active:translate-y-0"
  };
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold transition duration-200 disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  );
});

export const Card = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "rounded-[1.5rem] border border-slate-200 bg-white shadow-[0_14px_36px_rgba(15,23,42,0.05)] backdrop-blur",
      className
    )}
    {...props}
  />
);

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full rounded-xl border border-slate-200 bg-white/88 px-3.5 py-2.5 text-sm text-slate-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)] outline-none transition duration-200 placeholder:text-slate-400 focus:border-accent-400 focus:bg-white focus:ring-4 focus:ring-accent-100",
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
          "min-h-28 w-full rounded-xl border border-slate-200 bg-white/88 px-3.5 py-3 text-sm text-slate-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)] outline-none transition duration-200 placeholder:text-slate-400 focus:border-accent-400 focus:bg-white focus:ring-4 focus:ring-accent-100",
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
          "w-full rounded-xl border border-slate-200 bg-white/88 px-3.5 py-2.5 text-sm text-slate-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)] outline-none transition duration-200 focus:border-accent-400 focus:bg-white focus:ring-4 focus:ring-accent-100",
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
    neutral: "border border-slate-200 bg-white/88 text-slate-600",
    info: "border border-sky-200 bg-sky-50 text-sky-700",
    success: "border border-emerald-200 bg-emerald-50 text-emerald-700",
    warning: "border border-amber-200 bg-amber-50 text-amber-700",
    danger: "border border-rose-200 bg-rose-50 text-rose-700"
  };
  return <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-semibold", tones[tone], className)}>{children}</span>;
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
        "rounded-full px-3 py-1.5 text-sm font-semibold transition duration-200",
        active
          ? "bg-[linear-gradient(135deg,#2563eb,#1d4ed8)] text-white shadow-[0_10px_24px_rgba(37,99,235,0.22)]"
          : "border border-slate-200 bg-white/92 text-slate-600 hover:border-slate-300 hover:bg-white hover:text-slate-900",
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
