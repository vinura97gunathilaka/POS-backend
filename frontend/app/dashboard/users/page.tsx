'use client';

import React from 'react';
import { 
  Users, ShieldCheck, Plus, Edit, Trash2, ShieldAlert, 
  UserCheck, Shield, HelpCircle, Loader2, KeyRound
} from 'lucide-react';
import { usePOSStore } from '@/store/usePOSStore';
import { apiClient } from '@/services/api';
import { Button, Card, Input, Modal, Table, Toast, Select } from '@/components/UI';
import { hasPermission } from '@/utils/permissions';

export default function UsersRolesPage() {
  const { currentUser, activeCompany } = usePOSStore();
  
  // Navigation Tabs: 'users' | 'roles'
  const [activeTab, setActiveTab] = React.useState<'users' | 'roles'>('users');
  
  // Data lists
  const [users, setUsers] = React.useState<any[]>([]);
  const [roles, setRoles] = React.useState<any[]>([]);
  const [branches, setBranches] = React.useState<any[]>([]);
  const [permissions, setPermissions] = React.useState<any[]>([]);
  
  // Modals state
  const [isAddUserOpen, setIsAddUserOpen] = React.useState(false);
  const [isEditUserOpen, setIsEditUserOpen] = React.useState(false);
  const [isAddRoleOpen, setIsAddRoleOpen] = React.useState(false);
  const [isEditRoleOpen, setIsEditRoleOpen] = React.useState(false);
  
  // Selected items for editing
  const [selectedUser, setSelectedUser] = React.useState<any | null>(null);
  const [selectedRole, setSelectedRole] = React.useState<any | null>(null);

  // Form: User fields
  const [userName, setUserName] = React.useState('');
  const [userEmail, setUserEmail] = React.useState('');
  const [userPhone, setUserPhone] = React.useState('');
  const [userPassword, setUserPassword] = React.useState('');
  const [userStatus, setUserStatus] = React.useState('active');
  const [userRolesSelected, setUserRolesSelected] = React.useState<number[]>([]);
  const [userBranchesSelected, setUserBranchesSelected] = React.useState<number[]>([]);

  // Form: Role fields
  const [roleName, setRoleName] = React.useState('');
  const [roleDesc, setRoleDesc] = React.useState('');
  const [rolePermsSelected, setRolePermsSelected] = React.useState<number[]>([]);

  const [toastMsg, setToastMsg] = React.useState('');
  const [toastType, setToastType] = React.useState<'success' | 'error'>('success');
  const [isLoading, setIsLoading] = React.useState(false);

  // Fetch all necessary data
  const fetchData = async () => {
    try {
      const uRes = await apiClient.get('/users/');
      if (uRes.data.success && uRes.data.data) {
        setUsers(uRes.data.data);
      }
      
      const rRes = await apiClient.get('/users/roles');
      if (rRes.data.success && rRes.data.data) {
        setRoles(rRes.data.data);
      }

      const bRes = await apiClient.get('/branches/');
      if (bRes.data.success && bRes.data.data) {
        setBranches(bRes.data.data);
      }

      const pRes = await apiClient.get('/users/permissions');
      if (pRes.data.success && pRes.data.data) {
        setPermissions(pRes.data.data);
      }
    } catch (err) {}
  };

  React.useEffect(() => {
    if (currentUser && hasPermission(currentUser, 'users:manage')) {
      fetchData();
    }
  }, [currentUser]);

  const triggerToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToastMsg(msg);
    setToastType(type);
  };

  // Open modals & reset states
  const openAddUser = () => {
    setUserName('');
    setUserEmail('');
    setUserPhone('');
    setUserPassword('');
    setUserRolesSelected([]);
    setUserBranchesSelected(branches.length > 0 ? [branches[0].id] : []);
    setIsAddUserOpen(true);
  };

  const openEditUser = (user: any) => {
    setSelectedUser(user);
    setUserName(user.name);
    setUserEmail(user.email);
    setUserPhone(user.phone || '');
    setUserPassword('');
    setUserStatus(user.status || 'active');
    setUserRolesSelected(user.roles?.map((r: any) => r.id) || []);
    setUserBranchesSelected(user.branches?.map((b: any) => b.id) || []);
    setIsEditUserOpen(true);
  };

  const openAddRole = () => {
    setRoleName('');
    setRoleDesc('');
    setRolePermsSelected([]);
    setIsAddRoleOpen(true);
  };

  const openEditRole = (role: any) => {
    setSelectedRole(role);
    setRoleName(role.name);
    setRoleDesc(role.description || '');
    setRolePermsSelected(role.permissions?.map((p: any) => p.id) || []);
    setIsEditRoleOpen(true);
  };

  // User Actions
  const handleAddUser = async () => {
    if (!userName || !userEmail || !userPassword) {
      triggerToast('Name, Email and Password are required.', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        company_id: activeCompany.id,
        name: userName,
        email: userEmail,
        password: userPassword,
        phone: userPhone || null,
        is_superadmin: false,
        role_ids: userRolesSelected,
        branch_ids: userBranchesSelected
      };
      
      const res = await apiClient.post('/users/', payload);
      if (res.data.success) {
        triggerToast('User created successfully.');
        setIsAddUserOpen(false);
        fetchData();
      }
    } catch (err: any) {
      triggerToast(err.response?.data?.detail || 'Failed to create user.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditUser = async () => {
    if (!userName || !userEmail) {
      triggerToast('Name and Email are required.', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const payload: any = {
        name: userName,
        email: userEmail,
        phone: userPhone || null,
        status: userStatus,
        role_ids: userRolesSelected,
        branch_ids: userBranchesSelected
      };
      if (userPassword) {
        payload.password = userPassword;
      }
      
      const res = await apiClient.put(`/users/${selectedUser.id}`, payload);
      if (res.data.success) {
        triggerToast('User updated successfully.');
        setIsEditUserOpen(false);
        fetchData();
      }
    } catch (err: any) {
      triggerToast(err.response?.data?.detail || 'Failed to update user.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteUser = async (id: number) => {
    if (!confirm('Are you sure you want to archive this employee?')) return;
    try {
      const res = await apiClient.delete(`/users/${id}`);
      if (res.data.success) {
        triggerToast('User archived successfully.');
        fetchData();
      }
    } catch (err) {
      triggerToast('Failed to archive user.', 'error');
    }
  };

  // Role Actions
  const handleAddRole = async () => {
    if (!roleName) {
      triggerToast('Role name is required.', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        company_id: activeCompany.id,
        name: roleName,
        description: roleDesc,
        permission_ids: rolePermsSelected
      };
      const res = await apiClient.post('/users/roles', payload);
      if (res.data.success) {
        triggerToast('Role created successfully.');
        setIsAddRoleOpen(false);
        fetchData();
      }
    } catch (err) {
      triggerToast('Failed to create role.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditRole = async () => {
    if (!roleName) {
      triggerToast('Role name is required.', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        name: roleName,
        description: roleDesc,
        permission_ids: rolePermsSelected
      };
      const res = await apiClient.put(`/users/roles/${selectedRole.id}`, payload);
      if (res.data.success) {
        triggerToast('Role updated successfully.');
        setIsEditRoleOpen(false);
        fetchData();
      }
    } catch (err) {
      triggerToast('Failed to update role.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Checkbox handlers
  const handleRoleToggle = (roleId: number) => {
    setUserRolesSelected(prev => 
      prev.includes(roleId) ? prev.filter(id => id !== roleId) : [...prev, roleId]
    );
  };

  const handleBranchToggle = (branchId: number) => {
    setUserBranchesSelected(prev => 
      prev.includes(branchId) ? prev.filter(id => id !== branchId) : [...prev, branchId]
    );
  };

  const handlePermToggle = (permId: number) => {
    setRolePermsSelected(prev => 
      prev.includes(permId) ? prev.filter(id => id !== permId) : [...prev, permId]
    );
  };

  // Security Gate
  if (!currentUser || !hasPermission(currentUser, 'users:manage')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm text-left">
        <ShieldAlert className="w-16 h-16 text-red-500 mb-4 animate-bounce" />
        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Access Denied</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
          You do not have the required permissions (`users:manage`) to access the Users & Roles Management screen. Please contact your company administrator.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 text-left">
      
      {/* Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-bold dark:text-white">Users & Roles Control</h2>
          <p className="text-xs text-slate-400">Establish store employee profiles, specify custom security roles, and assign branch accesses.</p>
        </div>
        
        <div className="flex gap-2 shrink-0">
          {activeTab === 'users' ? (
            <Button onClick={openAddUser} icon={<Plus className="w-4 h-4" />}>
              Create User Profile
            </Button>
          ) : (
            <Button onClick={openAddRole} icon={<Plus className="w-4 h-4" />}>
              Add Custom Role
            </Button>
          )}
        </div>
      </div>

      {/* Tabs Selector Header */}
      <div className="flex border-b border-slate-100 dark:border-slate-800 gap-6">
        <button 
          onClick={() => setActiveTab('users')}
          className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
            activeTab === 'users' 
              ? 'border-brand-500 text-brand-600 dark:text-brand-400' 
              : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
          }`}
        >
          Employees Ledger
        </button>
        <button 
          onClick={() => setActiveTab('roles')}
          className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
            activeTab === 'roles' 
              ? 'border-brand-500 text-brand-600 dark:text-brand-400' 
              : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
          }`}
        >
          Roles & Permissions Config
        </button>
      </div>

      {/* TAB CONTENT 1: EMPLOYEES LEDGER */}
      {activeTab === 'users' && (
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-brand-500" />
            <h3 className="font-bold text-base text-slate-800 dark:text-white">Active Store Employees</h3>
          </div>
          <Table
            headers={["Name & Email", "Contact Number", "Assigned Roles", "Assigned Branches", "Status", "Actions"]}
            rows={users.map((u) => {
              const uRoles = u.roles?.map((r: any) => r.name).join(', ') || 'No Roles';
              const uBranches = u.branches?.map((b: any) => b.name).join(', ') || 'No Branch Access';
              const statusColors: any = {
                active: 'bg-emerald-500/10 text-emerald-500',
                inactive: 'bg-amber-500/10 text-amber-500',
                archived: 'bg-red-500/10 text-red-500'
              };
              return [
                <div key={1} className="flex flex-col">
                  <span className="font-semibold text-slate-800 dark:text-white flex items-center gap-1.5">
                    {u.name}
                    {u.is_superadmin && (
                      <span className="bg-indigo-500/10 text-indigo-500 text-[8px] font-bold uppercase px-1.5 py-0.5 rounded">Super</span>
                    )}
                  </span>
                  <span className="text-[10px] text-slate-400">{u.email}</span>
                </div>,
                <span key={2} className="text-xs text-slate-500 dark:text-slate-400">{u.phone || 'N/A'}</span>,
                <span key={3} className="text-xs text-slate-400 font-semibold">{uRoles}</span>,
                <span key={4} className="text-xs text-slate-400 font-semibold">{uBranches}</span>,
                <span key={5} className={`px-2 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider ${statusColors[u.status] || 'bg-slate-500/10 text-slate-500'}`}>
                  {u.status}
                </span>,
                <div key={6} className="flex gap-2">
                  <Button onClick={() => openEditUser(u)} variant="ghost" className="min-h-0 py-1.5 px-2.5 text-xs text-brand-500" icon={<Edit className="w-3.5 h-3.5" />}>
                    Edit
                  </Button>
                  {!u.is_superadmin && (
                    <Button onClick={() => handleDeleteUser(u.id)} variant="ghost" className="min-h-0 py-1.5 px-2.5 text-xs text-red-500" icon={<Trash2 className="w-3.5 h-3.5" />}>
                      Archive
                    </Button>
                  )}
                </div>
              ];
            })}
          />
        </Card>
      )}

      {/* TAB CONTENT 2: ROLES & PERMISSIONS */}
      {activeTab === 'roles' && (
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="w-5 h-5 text-brand-500" />
            <h3 className="font-bold text-base text-slate-800 dark:text-white">Configured Security Roles</h3>
          </div>
          <Table
            headers={["Role Name", "Description", "Assigned Privileges", "Actions"]}
            rows={roles.map((role) => {
              const count = role.permissions?.length || 0;
              const permsCodes = role.permissions?.map((p: any) => p.code).join(', ');
              return [
                <span key={1} className="font-bold text-slate-800 dark:text-white flex items-center gap-1.5">
                  <Shield className="w-4 h-4 text-brand-500" />
                  {role.name}
                </span>,
                <span key={2} className="text-xs text-slate-500 dark:text-slate-400 max-w-xs block truncate">{role.description || 'No description provided'}</span>,
                <div key={3} className="flex flex-col gap-1.5">
                  <span className="text-[10px] font-bold text-brand-500 bg-brand-500/10 px-2 py-0.5 rounded self-start">{count} permissions</span>
                  <span className="text-[9px] text-slate-400 font-mono max-w-lg block leading-relaxed">{permsCodes || 'None'}</span>
                </div>,
                <div key={4} className="flex gap-2">
                  <Button onClick={() => openEditRole(role)} variant="ghost" className="min-h-0 py-1.5 px-2.5 text-xs text-brand-500" icon={<Edit className="w-3.5 h-3.5" />}>
                    Edit Privilege Map
                  </Button>
                </div>
              ];
            })}
          />
        </Card>
      )}

      {/* MODAL: CREATE USER PROFILE */}
      <Modal isOpen={isAddUserOpen} onClose={() => setIsAddUserOpen(false)} title="Create Store Employee Profile">
        <div className="flex flex-col gap-4 text-left">
          <Input label="Employee Full Name" value={userName} onChange={(e) => setUserName(e.target.value)} placeholder="e.g. Ruwan Perera" />
          <Input label="Login Email Address" type="email" value={userEmail} onChange={(e) => setUserEmail(e.target.value)} placeholder="employee@smartpos.com" />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Contact Phone Number" value={userPhone} onChange={(e) => setUserPhone(e.target.value)} placeholder="e.g. +94777123456" />
            <Input label="Temporary Password" type="password" value={userPassword} onChange={(e) => setUserPassword(e.target.value)} placeholder="Min 6 characters" />
          </div>

          {/* Role Checkbox Selection */}
          <div className="flex flex-col gap-2 border-t border-slate-100 dark:border-slate-800 pt-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Assign Security Roles</span>
            <div className="grid grid-cols-2 gap-2">
              {roles.map(r => (
                <label key={r.id} className="flex items-center gap-2 px-3 py-2 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer text-sm font-semibold text-slate-700 dark:text-slate-300">
                  <input type="checkbox" checked={userRolesSelected.includes(r.id)} onChange={() => handleRoleToggle(r.id)} className="w-4 h-4 rounded text-brand-500 focus:ring-brand-500" />
                  {r.name}
                </label>
              ))}
            </div>
          </div>

          {/* Branch Checkbox Selection */}
          <div className="flex flex-col gap-2 border-t border-slate-100 dark:border-slate-800 pt-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Assign Branch Access</span>
            <div className="grid grid-cols-2 gap-2">
              {branches.map(b => (
                <label key={b.id} className="flex items-center gap-2 px-3 py-2 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer text-sm font-semibold text-slate-700 dark:text-slate-300">
                  <input type="checkbox" checked={userBranchesSelected.includes(b.id)} onChange={() => handleBranchToggle(b.id)} className="w-4 h-4 rounded text-brand-500 focus:ring-brand-500" />
                  {b.name}
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-4 border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button onClick={() => setIsAddUserOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleAddUser} isLoading={isLoading}>Save Profile</Button>
          </div>
        </div>
      </Modal>

      {/* MODAL: EDIT USER PROFILE */}
      <Modal isOpen={isEditUserOpen} onClose={() => setIsEditUserOpen(false)} title="Update Employee Profile">
        <div className="flex flex-col gap-4 text-left">
          <Input label="Employee Full Name" value={userName} onChange={(e) => setUserName(e.target.value)} />
          <Input label="Login Email Address" type="email" value={userEmail} onChange={(e) => setUserEmail(e.target.value)} />
          
          <div className="grid grid-cols-2 gap-4">
            <Input label="Contact Phone" value={userPhone} onChange={(e) => setUserPhone(e.target.value)} />
            <Select 
              label="Account Status"
              value={userStatus}
              onChange={(e) => setUserStatus(e.target.value)}
              options={[
                { label: "Active Status", value: "active" },
                { label: "Inactive/Deactivated", value: "inactive" }
              ]}
            />
          </div>

          <div className="p-3 border border-slate-100 dark:border-slate-800 rounded-2xl flex flex-col gap-2 bg-slate-50/30">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
              <KeyRound className="w-3.5 h-3.5 text-brand-500" /> Reset Password (Optional)
            </span>
            <Input type="password" value={userPassword} onChange={(e) => setUserPassword(e.target.value)} placeholder="Leave blank to retain existing password" />
          </div>

          {/* Role Checkbox Selection */}
          <div className="flex flex-col gap-2 border-t border-slate-100 dark:border-slate-800 pt-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Assign Security Roles</span>
            <div className="grid grid-cols-2 gap-2">
              {roles.map(r => (
                <label key={r.id} className="flex items-center gap-2 px-3 py-2 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer text-sm font-semibold text-slate-700 dark:text-slate-300">
                  <input type="checkbox" checked={userRolesSelected.includes(r.id)} onChange={() => handleRoleToggle(r.id)} className="w-4 h-4 rounded text-brand-500 focus:ring-brand-500" />
                  {r.name}
                </label>
              ))}
            </div>
          </div>

          {/* Branch Checkbox Selection */}
          <div className="flex flex-col gap-2 border-t border-slate-100 dark:border-slate-800 pt-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Assign Branch Access</span>
            <div className="grid grid-cols-2 gap-2">
              {branches.map(b => (
                <label key={b.id} className="flex items-center gap-2 px-3 py-2 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer text-sm font-semibold text-slate-700 dark:text-slate-300">
                  <input type="checkbox" checked={userBranchesSelected.includes(b.id)} onChange={() => handleBranchToggle(b.id)} className="w-4 h-4 rounded text-brand-500 focus:ring-brand-500" />
                  {b.name}
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-4 border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button onClick={() => setIsEditUserOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleEditUser} isLoading={isLoading}>Update Profile</Button>
          </div>
        </div>
      </Modal>

      {/* MODAL: ADD CUSTOM ROLE */}
      <Modal isOpen={isAddRoleOpen} onClose={() => setIsAddRoleOpen(false)} title="Create New Security Role">
        <div className="flex flex-col gap-4 text-left">
          <Input label="Role Identifier / Name" value={roleName} onChange={(e) => setRoleName(e.target.value)} placeholder="e.g. Cashier / Warehouse Admin" />
          <Input label="Role Description" value={roleDesc} onChange={(e) => setRoleDesc(e.target.value)} placeholder="Brief summary of duties and accesses" />

          {/* Permissions checkbox lists */}
          <div className="flex flex-col gap-2 border-t border-slate-100 dark:border-slate-800 pt-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Map Role Permissions</span>
            {permissions.length === 0 ? (
              <span className="text-xs text-slate-400">Loading privilege list...</span>
            ) : (
              <div className="grid grid-cols-1 gap-2 max-h-60 overflow-y-auto pr-1">
                {permissions.map(p => (
                  <label key={p.id} className="flex items-start gap-2.5 px-3 py-2 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer text-left">
                    <input type="checkbox" checked={rolePermsSelected.includes(p.id)} onChange={() => handlePermToggle(p.id)} className="w-4 h-4 rounded text-brand-500 focus:ring-brand-500 mt-0.5" />
                    <div className="flex flex-col">
                      <span className="text-xs font-bold text-slate-700 dark:text-slate-300">{p.name}</span>
                      <span className="text-[9px] text-slate-400 font-mono">{p.code} &mdash; {p.description}</span>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 mt-4 border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button onClick={() => setIsAddRoleOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleAddRole} isLoading={isLoading}>Save Role</Button>
          </div>
        </div>
      </Modal>

      {/* MODAL: EDIT CUSTOM ROLE */}
      <Modal isOpen={isEditRoleOpen} onClose={() => setIsEditRoleOpen(false)} title="Update Role & Privileges Map">
        <div className="flex flex-col gap-4 text-left">
          <Input label="Role Identifier / Name" value={roleName} onChange={(e) => setRoleName(e.target.value)} />
          <Input label="Role Description" value={roleDesc} onChange={(e) => setRoleDesc(e.target.value)} />

          {/* Permissions checkbox lists */}
          <div className="flex flex-col gap-2 border-t border-slate-100 dark:border-slate-800 pt-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Map Role Permissions</span>
            <div className="grid grid-cols-1 gap-2 max-h-60 overflow-y-auto pr-1">
              {permissions.map(p => (
                <label key={p.id} className="flex items-start gap-2.5 px-3 py-2 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer text-left">
                  <input type="checkbox" checked={rolePermsSelected.includes(p.id)} onChange={() => handlePermToggle(p.id)} className="w-4 h-4 rounded text-brand-500 focus:ring-brand-500 mt-0.5" />
                  <div className="flex flex-col">
                    <span className="text-xs font-bold text-slate-700 dark:text-slate-300">{p.name}</span>
                    <span className="text-[9px] text-slate-400 font-mono">{p.code} &mdash; {p.description}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-4 border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button onClick={() => setIsEditRoleOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleEditRole} isLoading={isLoading}>Save Mapping</Button>
          </div>
        </div>
      </Modal>

      {toastMsg && (
        <Toast
          message={toastMsg}
          onClose={() => setToastMsg('')}
          type={toastType}
        />
      )}

    </div>
  );
}
