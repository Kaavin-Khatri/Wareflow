/**
 * Navigation configuration with data-driven RBAC permission requirements.
 *
 * Each navigation item defines an optional `requiredPermission` or `requiredRole`.
 * Nav bars and Sidebars filter items against the caller's live permission set.
 */

export interface NavItem {
  name: string;
  href: string;
  icon?: string;
  badge?: string;
  requiredPermission?: string;
  requiredRole?: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const NAVIGATION_SECTIONS: NavSection[] = [
  {
    title: "Overview",
    items: [
      {
        name: "Dashboard",
        href: "/dashboard",
        icon: "LayoutDashboard",
      },
    ],
  },
  {
    title: "Wholesale Operations",
    items: [
      {
        name: "Product Catalog",
        href: "/admin/products",
        icon: "Package",
        requiredPermission: "inventory:view",
      },
      {
        name: "Categories",
        href: "/admin/categories",
        icon: "Tags",
        requiredPermission: "inventory:view",
      },
      {
        name: "Inventory & Stock",
        href: "/admin/inventory",
        icon: "Boxes",
        requiredPermission: "inventory:view",
      },
      {
        name: "Stock Analytics",
        href: "/admin/analytics/stock",
        icon: "BarChart3",
        requiredPermission: "inventory:view",
      },
      {
        name: "Orders & Dispatch",
        href: "/orders",
        icon: "ShoppingBag",
        requiredPermission: "orders:view",
      },
      {
        name: "GST Invoices",
        href: "/invoices",
        icon: "ReceiptText",
        requiredPermission: "invoices:view",
      },
      {
        name: "Returns & RMA",
        href: "/returns",
        icon: "RotateCcw",
        requiredPermission: "orders:view",
      },
    ],
  },
  {
    title: "Organization & Admin",
    items: [
      {
        name: "Staff Management",
        href: "/admin/settings/staff",
        icon: "Users",
        requiredPermission: "staff:view",
      },
      {
        name: "Permission Matrix",
        href: "/admin/settings/permissions",
        icon: "ShieldCheck",
        requiredPermission: "settings:manage",
      },
      {
        name: "Security & 2FA",
        href: "/admin/settings/security",
        icon: "KeyRound",
        requiredPermission: "settings:manage",
      },
      {
        name: "Audit Log",
        href: "/admin/audit",
        icon: "History",
        requiredPermission: "audit:view",
      },
      {
        name: "Appearance & Theme",
        href: "/admin/settings/appearance",
        icon: "Sparkles",
        requiredPermission: "settings:manage",
      },

      {
        name: "Business Settings",
        href: "/admin/settings/business",
        icon: "Building2",
        requiredPermission: "settings:manage",
      },
      {
        name: "Design System",
        href: "/styleguide",
        icon: "Palette",
        badge: "v4.2",
        requiredRole: "Owner",
      },
    ],
  },
];

/**
 * Filter navigation items dynamically based on a user's permissions and role.
 */
export function filterNavSections(
  sections: NavSection[],
  userPermissions: string[] | Set<string>,
  userRole?: string,
): NavSection[] {
  const permSet = userPermissions instanceof Set ? userPermissions : new Set(userPermissions);
  const isOwner = userRole?.toLowerCase() === "owner";

  return sections
    .map((section) => {
      const visibleItems = section.items.filter((item) => {
        // Owner has uninhibited root access to all sections
        if (isOwner) return true;

        if (item.requiredRole && item.requiredRole !== userRole) {
          return false;
        }

        if (item.requiredPermission && !permSet.has(item.requiredPermission)) {
          return false;
        }

        return true;
      });

      return {
        ...section,
        items: visibleItems,
      };
    })
    .filter((section) => section.items.length > 0);
}
