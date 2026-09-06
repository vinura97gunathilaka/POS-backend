export function hasPermission(user: any, permissionCode: string): boolean {
  if (!user) return false;
  if (user.is_superadmin) return true;
  return user.roles?.some((role: any) =>
    role.permissions?.some((perm: any) => perm.code === permissionCode)
  ) || false;
}
