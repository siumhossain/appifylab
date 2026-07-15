import { cn } from "@/lib/utils";

export function Avatar({
  firstName,
  lastName,
  className,
  ring = false,
}: {
  firstName: string;
  lastName: string;
  className?: string;
  ring?: boolean;
}) {
  const initials = `${firstName[0] ?? ""}${lastName[0] ?? ""}`.toUpperCase();
  const face = (
    <div
      className={cn(
        "flex items-center justify-center rounded-full bg-gradient-to-br from-neutral-200 to-neutral-300 font-semibold text-neutral-600 select-none dark:from-neutral-700 dark:to-neutral-800 dark:text-neutral-200",
        className ?? "size-9 text-xs"
      )}
    >
      {initials}
    </div>
  );
  if (!ring) return face;
  return (
    <div className="rounded-full bg-gradient-to-tr from-amber-400 via-rose-500 to-purple-600 p-[2px]">
      <div className="rounded-full bg-card p-[2px]">{face}</div>
    </div>
  );
}
