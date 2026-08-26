"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassInput } from "@/components/glass/GlassInput";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassSelect } from "@/components/glass/GlassSelect";
import { apiClient } from "@/lib/api-client";
import { Plus, Edit2, Trash2, FolderTree, Layers } from "lucide-react";

export interface CategoryItem {
  id: string;
  name: string;
  parent_id: string | null;
  created_at?: string;
}

export default function CategoriesPage() {
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<CategoryItem | null>(null);
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchCategories = async () => {
    try {
      const data = await apiClient.get<CategoryItem[]>("/categories");
      setCategories(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load categories.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();

    const handle2FAVerified = () => {
      setError(null);
      fetchCategories();
    };

    window.addEventListener("wareflow:2fa-verified", handle2FAVerified);
    return () => {
      window.removeEventListener("wareflow:2fa-verified", handle2FAVerified);
    };
  }, []);

  const handleOpenCreate = () => {
    setEditingCategory(null);
    setName("");
    setParentId("");
    setModalOpen(true);
  };

  const handleOpenEdit = (category: CategoryItem) => {
    setEditingCategory(category);
    setName(category.name);
    setParentId(category.parent_id || "");
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = {
        name: name.trim(),
        parent_id: parentId.trim() ? parentId.trim() : null,
      };

      if (editingCategory) {
        await apiClient.patch(`/categories/${editingCategory.id}`, payload);
        setSuccess(`Category "${name}" updated successfully.`);
      } else {
        await apiClient.post("/categories", payload);
        setSuccess(`Category "${name}" created successfully.`);
      }

      setModalOpen(false);
      await fetchCategories();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save category.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (category: CategoryItem) => {
    if (!confirm(`Are you sure you want to delete "${category.name}"?`)) return;

    setError(null);
    try {
      await apiClient.delete(`/categories/${category.id}`);
      setSuccess(`Category "${category.name}" deleted.`);
      await fetchCategories();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete category.");
    }
  };

  const filteredCategories = categories.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const columns: DataTableColumn<CategoryItem>[] = [
    {
      key: "name",
      header: "Category Name",
      mobilePrimary: true,
      sortable: true,
      render: (item) => (
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-purple-400 shrink-0" />
          <span className="font-semibold text-white">{item.name}</span>
        </div>
      ),
    },
    {
      key: "parent",
      header: "Parent Category",
      sortable: true,
      render: (item) => {
        if (!item.parent_id) return <span className="text-white/40 text-xs">Root Level</span>;
        const parent = categories.find((c) => c.id === item.parent_id);
        return (
          <span className="text-purple-300 text-xs font-mono">{parent?.name || "Parent"}</span>
        );
      },
    },
    {
      key: "created_at",
      header: "Created Date",
      sortable: true,
      render: (item) => (
        <span className="text-white/50 text-xs font-mono">
          {item.created_at ? new Date(item.created_at).toLocaleDateString() : "—"}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (item) => (
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={() => handleOpenEdit(item)}
            className="p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
            title="Edit Category"
            aria-label={`Edit ${item.name}`}
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => handleDelete(item)}
            className="p-1.5 rounded-lg text-red-400/70 hover:text-red-300 hover:bg-red-500/10 transition-colors"
            title="Delete Category"
            aria-label={`Delete ${item.name}`}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <AppLayout>
      <ListViewTemplate
        title="Product Categories"
        description="Organize your wholesale product hierarchy and catalog taxonomy."
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search categories..."
        primaryAction={
          <GlassButton onClick={handleOpenCreate} variant="primary">
            <Plus className="w-4 h-4 mr-1.5 inline" /> Add Category
          </GlassButton>
        }
      >
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm">
            {success}
          </div>
        )}

        <DataTable
          columns={columns}
          data={filteredCategories}
          keyExtractor={(item) => item.id}
          isLoading={loading}
          emptyTitle="No categories found"
          emptyDescription="Start structuring your catalog by adding your first product category."
          emptyIcon={<FolderTree className="w-12 h-12 text-purple-400/50" />}
          emptyAction={
            <GlassButton onClick={handleOpenCreate} variant="primary">
              <Plus className="w-4 h-4 mr-1.5 inline" /> Create Category
            </GlassButton>
          }
        />
      </ListViewTemplate>

      {/* Category Create/Edit Modal */}
      <GlassModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingCategory ? "Edit Category" : "Add New Category"}
        description="Configure taxonomy node name and parent nesting hierarchy."
        maxWidth="md"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
              Category Name
            </label>
            <GlassInput
              placeholder="e.g. Grains & Basmati Rice"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
              Parent Category (Optional)
            </label>
            <GlassSelect
              value={parentId}
              onChange={setParentId}
              options={[
                { value: "", label: "None (Top-Level Category)" },
                ...categories
                  .filter((c) => !editingCategory || c.id !== editingCategory.id)
                  .map((c) => ({ value: c.id, label: c.name })),
              ]}
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
            <GlassButton type="button" variant="ghost" onClick={() => setModalOpen(false)}>
              Cancel
            </GlassButton>
            <GlassButton type="submit" variant="primary" disabled={submitting}>
              {submitting ? "Saving..." : editingCategory ? "Update Category" : "Create Category"}
            </GlassButton>
          </div>
        </form>
      </GlassModal>
    </AppLayout>
  );
}
