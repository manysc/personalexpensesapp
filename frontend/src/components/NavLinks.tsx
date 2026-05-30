"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard", exact: true },
  { href: "/expenses", label: "Expenses", exact: false },
  { href: "/rentals", label: "Rentals", exact: false },
  { href: "/vehicles", label: "Vehicles", exact: false },
  { href: "/categories", label: "Categories", exact: false },
  { href: "/import", label: "Import", exact: false },
];

export default function NavLinks() {
  const pathname = usePathname();

  return (
    <>
      {links.map(({ href, label, exact }) => {
        const active = exact ? pathname === href : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={`text-sm font-medium transition-colors ${
              active
                ? "text-blue-600 border-b-2 border-blue-600 pb-0.5"
                : "text-gray-600 hover:text-blue-600"
            }`}
          >
            {label}
          </Link>
        );
      })}
    </>
  );
}
