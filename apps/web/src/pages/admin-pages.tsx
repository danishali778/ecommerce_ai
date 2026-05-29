import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bell, Building2, Search, UserCog, UsersRound } from "lucide-react";

import { Badge, Button, Card, Checkbox, Input, Select } from "@frontend/ui";
import {
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  MetricCard,
  PageHeader,
  SectionCard,
  StatusPill,
  UserPill
} from "@/components/common";
import { useMarkNotificationRead, useNotifications } from "@/hooks/use-notifications";
import { useCreateOrganization, useCurrentOrganization } from "@/hooks/use-organization";
import { useCreateUser, useRoles, useUpdateUser, useUsers } from "@/hooks/use-users";
import { formatDate } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

export function NotificationsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const notificationsQuery = useNotifications(statusFilter || undefined);
  const markRead = useMarkNotificationRead();

  const notifications = notificationsQuery.data ?? [];
  const unreadCount = notifications.filter((notification) => !notification.read_at).length;
  const readCount = notifications.filter((notification) => Boolean(notification.read_at)).length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Notifications"
        description="Review workflow events, sync notices, and system alerts, then mark them read once the related work is complete."
        actions={
          <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="w-44">
            <option value="">All notifications</option>
            <option value="unread">Unread</option>
            <option value="read">Read</option>
          </Select>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Unread" value={unreadCount} hint="Still needs operator attention" tone={unreadCount ? "warning" : "success"} />
        <MetricCard label="Read" value={readCount} hint="Acknowledged in the current workspace" tone="info" />
        <MetricCard label="Total" value={notifications.length} hint="Notifications returned by the active filter" />
      </div>

      {notificationsQuery.isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : notificationsQuery.isError ? (
        <ErrorState title="Could not load notifications" message={messageFromError(notificationsQuery.error)} />
      ) : notifications.length === 0 ? (
        <EmptyState title="No notifications" message="System alerts, sync notices, and workflow updates will appear here." />
      ) : (
        <SectionCard title="Notification center">
          <div className="space-y-3">
            {notifications.map((notification) => (
              <Card key={notification.id} className={`p-4 ${notification.read_at ? "bg-white" : "border-amber-200 bg-amber-50/50"}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-white text-accent-700 shadow-sm">
                        <Bell className="h-4 w-4" />
                      </span>
                      <div>
                        <p className="font-semibold text-slate-950">{notification.title}</p>
                        <p className="text-xs text-slate-500">
                          {notification.type.replaceAll("_", " ")} - {formatDate(notification.created_at)}
                        </p>
                      </div>
                    </div>
                    <p className="text-sm leading-7 text-slate-600">{notification.body}</p>
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusPill value={notification.status} />
                      <Badge tone="info">{notification.channel.replaceAll("_", " ")}</Badge>
                      {notification.store_id ? <Badge tone="neutral">Store scoped</Badge> : null}
                    </div>
                  </div>
                  {notification.read_at ? (
                    <div className="text-right text-xs text-slate-500">
                      <p>Read</p>
                      <p>{formatDate(notification.read_at)}</p>
                    </div>
                  ) : (
                    <Button variant="secondary" onClick={() => markRead.mutate(notification.id)} disabled={markRead.isPending}>
                      Mark as read
                    </Button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}

export function OrganizationPage() {
  const [form, setForm] = useState({ name: "", slug: "" });

  const organizationQuery = useCurrentOrganization();
  const createOrganization = useCreateOrganization();

  return (
    <div className="space-y-8">
      <PageHeader title="Organization" description="Review or bootstrap the current organization context for the CommerceOps workspace." />

      {organizationQuery.isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : organizationQuery.data ? (
        <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <DetailPanel title="Current organization" subtitle="Workspace identity and lifecycle metadata">
            <KeyValueGrid
              items={[
                { label: "Name", value: organizationQuery.data.name },
                { label: "Slug", value: organizationQuery.data.slug },
                { label: "Status", value: <StatusPill value={organizationQuery.data.status} /> },
                { label: "Created", value: formatDate(organizationQuery.data.created_at) },
                { label: "Updated", value: formatDate(organizationQuery.data.updated_at) }
              ]}
            />
          </DetailPanel>

          <SectionCard title="Operational notes">
            <div className="space-y-4 text-sm text-slate-600">
              <Card className="border-blue-100 bg-blue-50 p-4">
                <div className="flex items-start gap-3">
                  <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-white text-accent-700 shadow-sm">
                    <Building2 className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="font-medium text-slate-950">Organization state</p>
                    <p className="mt-2 leading-7">
                      This workspace is already bootstrapped. Store access, role assignment, notifications, and runtime auditability inherit from this organization context.
                    </p>
                  </div>
                </div>
              </Card>
              <Card className="p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">What to do next</p>
                <p className="mt-2 leading-7 text-slate-700">
                  Continue with user provisioning, role assignment, and store onboarding from the rest of the internal console.
                </p>
              </Card>
            </div>
          </SectionCard>
        </div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <DetailPanel title="Bootstrap organization" subtitle="Create the base organization before provisioning internal access.">
            <div className="space-y-3 text-sm leading-7 text-slate-600">
              <p>CommerceOps uses organization context to scope users, stores, roles, notifications, and runtime history.</p>
              <p>Create the organization once, then continue configuring users and connected stores from the app shell.</p>
            </div>
          </DetailPanel>

          <SectionCard title="Create organization">
            <div className="space-y-4">
              <Input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="CommerceOps HQ" />
              <Input value={form.slug} onChange={(event) => setForm((current) => ({ ...current, slug: event.target.value }))} placeholder="commerceops-hq" />
              <Button onClick={() => createOrganization.mutate(form)} disabled={createOrganization.isPending}>
                {createOrganization.isPending ? "Creating..." : "Create organization"}
              </Button>
              {createOrganization.isError ? (
                <p className="text-sm text-rose-700">{messageFromError(createOrganization.error)}</p>
              ) : organizationQuery.isError ? (
                <p className="text-sm text-slate-500">No organization exists yet. Create one to continue provisioning the workspace.</p>
              ) : null}
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}

export function UsersPage() {
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [form, setForm] = useState({ email: "", full_name: "", role_names: [] as string[] });

  const rolesQuery = useRoles();
  const usersQuery = useUsers(search || undefined, roleFilter || undefined);
  const createUser = useCreateUser(() => {
    setForm({ email: "", full_name: "", role_names: [] });
  });

  const roles = rolesQuery.data ?? [];
  const users = usersQuery.data ?? [];
  const activeCount = users.filter((user) => user.status === "active").length;
  const invitedCount = users.filter((user) => user.status === "invited").length;
  const disabledCount = users.filter((user) => user.status === "disabled").length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Users and roles"
        description="Provision internal operators, assign role sets, and keep access aligned with the current organization."
        actions={
          <div className="flex flex-wrap gap-3">
            <div className="relative min-w-56">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search users" />
            </div>
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

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Active" value={activeCount} hint="Operators currently enabled" tone={activeCount ? "success" : "neutral"} />
        <MetricCard label="Invited" value={invitedCount} hint="Accounts waiting on activation or first sign-in" tone={invitedCount ? "warning" : "neutral"} />
        <MetricCard label="Disabled" value={disabledCount} hint="Accounts intentionally removed from current access" tone={disabledCount ? "danger" : "neutral"} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
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
                <Link
                  key={user.id}
                  to={`/app/users/${user.id}`}
                  className="block rounded-2xl border border-slate-200 p-4 transition hover:border-accent-300 hover:bg-accent-50"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-2">
                      <UserPill name={user.full_name} />
                      <p className="text-sm text-slate-600">{user.email}</p>
                      <div className="flex flex-wrap gap-2">
                        <StatusPill value={user.status} />
                        {user.roles.map((role) => (
                          <Badge key={role} tone="neutral">
                            {role}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <p className="text-xs text-slate-500">{formatDate(user.updated_at)}</p>
                  </div>
                </Link>
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
            <Button onClick={() => createUser.mutate(form)} disabled={createUser.isPending}>
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
  const [draft, setDraft] = useState({ full_name: "", status: "active", role_names: [] as string[] });

  const rolesQuery = useRoles();
  const usersQuery = useUsers();

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

  const updateUser = useUpdateUser(userId);

  if (usersQuery.isLoading) return <LoadingSkeleton rows={4} />;
  if (usersQuery.isError || !user) {
    return <ErrorState title="Could not load user" message={messageFromError(usersQuery.error)} />;
  }

  return (
    <div className="space-y-8">
      <PageHeader title={user.full_name} description="Review internal access metadata, role assignments, and account state." />

      <div className="grid gap-6 xl:grid-cols-[0.84fr_1.16fr]">
        <div className="space-y-6">
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

          <SectionCard title="Assigned roles">
            <div className="flex flex-wrap gap-2">
              {user.roles.length ? user.roles.map((role) => <Badge key={role} tone="neutral">{role}</Badge>) : <p className="text-sm text-slate-500">No roles assigned.</p>}
            </div>
          </SectionCard>
        </div>

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
            <div className="flex items-center gap-3">
              <Button onClick={() => updateUser.mutate(draft)} disabled={updateUser.isPending}>
                {updateUser.isPending ? "Saving..." : "Save changes"}
              </Button>
              <p className="text-sm text-slate-500">User detail continues to resolve from the current users list because the backend does not expose a dedicated detail endpoint.</p>
            </div>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
