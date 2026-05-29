import { Avatar } from "@frontend/ui";

export function UserPill({ name }: { name: string }) {
  return (
    <div className="inline-flex items-center gap-2">
      <Avatar name={name} />
      <span>{name}</span>
    </div>
  );
}
