import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names with Tailwind CSS conflict resolution.
 * Uses clsx for conditional classes and tailwind-merge to dedupe Tailwind classes.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
