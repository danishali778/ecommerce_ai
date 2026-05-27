import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { notificationsApi, orgApi, usersApi } from "@frontend/api-client";
import { Button, Checkbox, Input, Select } from "@frontend/ui";
import {
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  PageHeader,
  SectionCard,
  StatusPill,
  UserPill
} from "@/components/common";
import { formatDate } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const notificationsQuery = useQuery({
    queryKey: ["notifications", statusFilter],
    queryFn: () => notificationsApi.list({ status: statusFilter || undefined })
  });

  const markRead = useMutation({
    mutationFn: (notificationId: string) => notificationsApi.markRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    }
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title="Notifications"
        description="Review recent system notifications and mark them as read once the relevant operational work is complete."
        actions={
          <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="w-44">
            <option value="">All notifications</option>
            <option value="unread">Unread</option>
            <option value="read">Read</option>
          </Select>
        }
      />

      {notificationsQuery.isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : notificationsQuery.isError ? (
        <ErrorState title="Could not load notifications" message={messageFromError(notificationsQuery.error)} />
      ) : (notificationsQuery.data ?? []).length === 0 ? (
        <EmptyState title="No notifications" message="System alerts, sync notices, and workflow updates will appear here." />
      ) : (
        <SectionCard title="Recent notifications">
          <div className="space-y-3">
            {(notificationsQuery.data ?? []).map((notification) => (
              <div key={notification.id} className="rounded-2xl border border-slate-200 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-slate-950">{notification.title}</p>
                      <StatusPill value={notification.status} />
                    </div>
                    <p className="text-sm text-slate-600">{notification.body}</p>
                    <p className="text-xs text-slate-500">
                      {notification.type} · {formatDate(notification.created_at)}
                    </p>
                  </div>
                  {notification.read_at ? (
                    <p className="text-xs text-slate-500">Read {formatDate(notification.read_at)}</p>
                  ) : (
                    <Button variant="secondary" onClick={() => markRead.mutate(notification.id)} disabled={markRead.isPending}>
                      Mark as read
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}

export function OrganizationPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ name: "", slug: "" });

  const organizationQuery = useQuery({
    queryKey: ["organization", "current"],
    queryFn: () => orgApi.getCurrent(),
    retry: false
  });

  const createOrganization = useMutation({
    mutationFn: () => orgApi.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organization", "current"] });
    }
  });

  return (
    <div className="space-y-8">
      <PageHeader title="Organization" description="Bootstrap or review the current organization context for the CommerceOps workspace." />

      {organizationQuery.isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : organizationQuery.data ? (
        <SectionCard title="Current organization">
          <KeyValueGrid
            items={[
              { label: "Name", value: organizationQuery.data.name },
              { label: "Slug", value: organizationQuery.data.slug },
              { label: "Status", value: <StatusPill value={organizationQuery.data.status} /> },
              { label: "Created", value: formatDate(organizationQuery.data.created_at) }
            ]}
          />
        </SectionCard>
      ) : (
        <SectionCard title="Create organization">
          <div className="space-y-4">
            <Input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="CommerceOps HQ" />
            <Input value={form.slug} onChange={(event) => setForm((current) => ({ ...current, slug: event.target.value }))} placeholder="commerceops-hq" />
            <Button onClick={() => createOrganization.mutate()} disabled={createOrganization.isPending}>
              {createOrganization.isPending ? "Creating..." : "Create organization"}
            </Button>
            {createOrganization.isError ? (
              <p className="text-sm text-rose-700">{messageFromError(createOrganization.error)}</p>
            ) : organizationQuery.isError ? (
              <p className="text-sm text-slate-500">No organization found yet. Create one to continue configuring internal access.</p>
            ) : null}
          </div>
        </SectionCard>
      )}
    </div>
  );
}

export function UsersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [form, setForm] = useState({ email: "", full_name: "", role_names: [] as string[] });

  const rolesQuery = useQuery({
    queryKey: ["users", "roles"],
    queryFn: () => usersApi.listRoles()
  });

  const usersQuery = useQuery({
    queryKey: ["users", "list", search, roleFilter],
    queryFn: () => usersApi.list({ q: search || undefined, role: roleFilter || undefined })
  });

  const createUser = useMutation({
    mutationFn: () => usersApi.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "list"] });
      setForm({ email: "", full_name: "", role_names: [] });
    }
  });

  const roles = rolesQuery.data ?? [];
  const users = usersQuery.data ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Users and roles"
        description="Manage internal operators, role assignments, and access visibility."
        actions={
          <div className="flex flex-wrap gap-3">
            <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search users" />
            <Select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)} className="w-48">
              <option value="">All roles</option>
              {roles.map((role) => (
                <option key={role.name} value={role.name}>
                  {role.name}
                </option>
              ))}
            </Select>
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <SectionCard title="Internal users">
          {usersQuery.isLoading ? (
            <LoadingSkeleton rows={4} />
          ) : usersQuery.isError ? (
            <ErrorState title="Could not load users" message={messageFromError(usersQuery.error)} />
          ) : users.length === 0 ? (
            <EmptyState title="No users found" message="Create the first internal operator to start collaborating in the workspace." />
          ) : (
            <div className="space-y-3">
              {users.map((user) => (
                <a key={user.id} href={`/app/users/${user.id}`} className="block rounded-2xl border border-slate-200 p-4 transition hover:border-accent-300 hover:bg-accent-50">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <UserPill name={user.full_name} />
                      <p className="mt-2 text-sm text-slate-600">{user.email}</p>
                    </div>
                    <StatusPill value={user.status} />
                  </div>
                </a>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Create user">
          <div className="space-y-4">
            <Input value={form.full_name} onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))} placeholder="Full name" />
            <Input value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} placeholder="operator@company.com" />
            <div className="space-y-3">
              <p className="text-sm font-medium text-slate-700">Assign roles</p>
              {roles.map((role) => (
                <label key={role.name} className="flex items-start gap-3 rounded-2xl border border-slate-200 p-3">
                  <Checkbox
                    checked={form.role_names.includes(role.name)}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        role_names: event.target.checked
                          ? [...current.role_names, role.name]
                          : current.role_names.filter((value) => value !== role.name)
                      }))
                    }
                  />
                  <div>
                    <p className="font-medium text-slate-900">{role.name}</p>
                    <p className="text-sm text-slate-600">{role.description}</p>
                  </div>
                </label>
              ))}
            </div>
            <Button onClick={() => createUser.mutate()} disabled={createUser.isPending}>
              {createUser.isPending ? "Creating..." : "Create user"}
            </Button>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

export function UserDetailPage() {
  const { userId = "" } = useParams();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState({ full_name: "", status: "active", role_names: [] as string[] });

  const rolesQuery = useQuery({
    queryKey: ["users", "roles"],
    queryFn: () => usersApi.listRoles()
  });

  const usersQuery = useQuery({
    queryKey: ["users", "list", "detail"],
    queryFn: () => usersApi.list()
  });

  const user = useMemo(() => (usersQuery.data ?? []).find((entry) => entry.id === userId) ?? null, [usersQuery.data, userId]);

  useEffect(() => {
    if (user) {
      setDraft({
        full_name: user.full_name,
        status: user.status,
        role_names: user.roles
      });
    }
  }, [user]);

  const updateUser = useMutation({
    mutationFn: () => usersApi.update(userId, draft),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "list"] });
    }
  });

  if (usersQuery.isLoading) return <LoadingSkeleton rows={4} />;
  if (usersQuery.isError || !user) {
    return <ErrorState title="Could not load user" message={messageFromError(usersQuery.error)} />;
  }

  return (
    <div className="space-y-8">
      <PageHeader title={user.full_name} description="Review internal access metadata and update status or role assignments." />

      <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <DetailPanel title="User profile" subtitle="Current account summary">
          <KeyValueGrid
            items={[
              { label: "Email", value: user.email },
              { label: "Status", value: <StatusPill value={user.status} /> },
              { label: "Created", value: formatDate(user.created_at) },
              { label: "Updated", value: formatDate(user.updated_at) }
            ]}
          />
        </DetailPanel>

        <SectionCard title="Update user">
          <div className="space-y-4">
            <Input value={draft.full_name} onChange={(event) => setDraft((current) => ({ ...current, full_name: event.target.value }))} />
            <Select value={draft.status} onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value }))}>
              <option value="active">Active</option>
              <option value="invited">Invited</option>
              <option value="disabled">Disabled</option>
            </Select>
            <div className="space-y-3">
              {rolesQuery.data?.map((role) => (
                <label key={role.name} className="flex items-start gap-3 rounded-2xl border border-slate-200 p-3">
                  <Checkbox
                    checked={draft.role_names.includes(role.name)}
                    onChange={(event) =>
                      setDraft((current) => ({
                        ...current,
                        role_names: event.target.checked
                          ? [...current.role_names, role.name]
                          : current.role_names.filter((value) => value !== role.name)
                      }))
                    }
                  />
                  <div>
                    <p className="font-medium text-slate-900">{role.name}</p>
                    <p className="text-sm text-slate-600">{role.description}</p>
                  </div>
                </label>
              ))}
            </div>
            <Button onClick={() => updateUser.mutate()} disabled={updateUser.isPending}>
              {updateUser.isPending ? "Saving..." : "Save changes"}
            </Button>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
