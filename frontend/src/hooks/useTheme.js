import { useCallback, useState } from "react";

/** Dark/light theme state, persisted in localStorage and applied as a class on <html>. */
export function useTheme() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));

  const toggle = useCallback(() => {
    setDark((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle("dark", next);
      localStorage.setItem("theme", next ? "dark" : "light");
      return next;
    });
  }, []);

  return { dark, toggle };
}
