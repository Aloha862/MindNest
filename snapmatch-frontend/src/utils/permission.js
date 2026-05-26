export function roleHome(role) {
  return role === 'admin' ? '/admin/dashboard' : '/user/dashboard'
}

export function canAccessAdmin(user) {
  return user?.role === 'admin'
}
