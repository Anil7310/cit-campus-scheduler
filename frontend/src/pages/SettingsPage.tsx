import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  Settings,
  ShieldAlert,
  Sliders,
  History,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Lock,
  UserPlus,
  Users,
  KeyRound,
  Shield,
  GraduationCap,
  Calendar,
  Sparkles,
  RefreshCw,
  Building
} from 'lucide-react';

interface AuditLog {
  id: string;
  action: string;
  user: string;
  details: string;
  timestamp: string;
}

interface SystemUserItem {
  id: string;
  name: string;
  username: string;
  email: string;
  role: string;
  department: string;
  faculty_id?: string;
  qualifications?: string[];
  fields_of_interest?: string[];
  is_active: boolean;
  created_at?: string;
}

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // Solver weights
  const [spreadWeight, setSpreadWeight] = useState(40);
  const [loadWeight, setLoadWeight] = useState(30);
  const [morningWeight, setMorningWeight] = useState(20);
  const [gapWeight, setGapWeight] = useState(10);

  // System Users state
  const [systemUsers, setSystemUsers] = useState<SystemUserItem[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  
  // New user form state
  const [newName, setNewName] = useState('');
  const [newUsername, setNewUsername] = useState('');
  const [newRole, setNewRole] = useState<'faculty' | 'coordinator' | 'club' | 'admin'>('faculty');
  const [newDept, setNewDept] = useState('CSE');
  const [newFacultyId, setNewFacultyId] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newQualifications, setNewQualifications] = useState('');
  const [newFieldsOfInterest, setNewFieldsOfInterest] = useState('');
  const [createUserLoading, setCreateUserLoading] = useState(false);
  const [createUserError, setCreateUserError] = useState<string | null>(null);
  const [createdCredential, setCreatedCredential] = useState<{
    name: string;
    username: string;
    role: string;
    password: string;
  } | null>(null);

  // Audit logs state
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  // Reset Modal
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetInput, setResetInput] = useState('');
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState<string | null>(null);

  const fetchUsers = async () => {
    if (!isAdmin) return;
    setLoadingUsers(true);
    try {
      const uList = await api.getSystemUsers();
      setSystemUsers(uList);
    } catch (err) {
      console.error('Failed to load system users:', err);
    } finally {
      setLoadingUsers(false);
    }
  };

  const fetchLogs = async () => {
    setLoadingLogs(true);
    try {
      const audit = await api.getAuditLogs().catch(() => []);
      if (audit && audit.length > 0) {
        setLogs(
          audit.slice(0, 15).map((l: any, idx: number) => ({
            id: l._id || `LOG-${idx}`,
            action: l.action || 'SYSTEM_EVENT',
            user: l.actor_email || l.actor_id || 'system',
            details: typeof l.details === 'object' ? JSON.stringify(l.details) : String(l.details || ''),
            timestamp: l.ts ? new Date(l.ts).toLocaleTimeString() : 'Recent'
          }))
        );
      }
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchLogs();
  }, [isAdmin]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim() || !newName.trim() || !newPassword.trim()) {
      setCreateUserError('Please provide full name, username, and initial password.');
      return;
    }

    setCreateUserLoading(true);
    setCreateUserError(null);
    try {
      await api.createSystemUser({
        name: newName.trim(),
        username: newUsername.trim().toLowerCase(),
        role: newRole,
        department: newDept,
        faculty_id: newRole === 'faculty' ? newFacultyId.trim() || undefined : undefined,
        qualifications: newQualifications
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        fields_of_interest: newFieldsOfInterest
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        password: newPassword.trim(),
      });

      setCreatedCredential({
        name: newName.trim(),
        username: newUsername.trim().toLowerCase(),
        role: newRole,
        password: newPassword.trim()
      });

      // Reset form
      setNewName('');
      setNewUsername('');
      setNewPassword('');
      setNewFacultyId('');
      setNewQualifications('');
      setNewFieldsOfInterest('');
      fetchUsers();
      fetchLogs();
    } catch (err: any) {
      setCreateUserError(err.message || 'Failed to create member account');
    } finally {
      setCreateUserLoading(false);
    }
  };

  const handleResetConfirm = async () => {
    if (resetInput !== 'RESET') return;
    setResetting(true);
    try {
      await api.resetDemoData();
      setResetSuccess('Demo dataset successfully restored to pristine state!');
      setShowResetModal(false);
      setResetInput('');
      fetchUsers();
      fetchLogs();
    } catch (e: any) {
      console.error(e);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
              System Settings & Governance
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
              Administrative Console
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Manage institutional member credentials, configure optimization weights, and monitor audit logs
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={() => {
              setShowAddUserModal(true);
              setCreatedCredential(null);
              setCreateUserError(null);
            }}
            className="px-4 py-2 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-md shadow-brand-500/20 flex items-center space-x-2 transition-all shrink-0"
          >
            <UserPlus className="w-4 h-4" />
            <span>Add New Member</span>
          </button>
        )}
      </div>

      {resetSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span className="font-semibold">{resetSuccess}</span>
        </div>
      )}

      {/* MEMBER MANAGEMENT SECTION (ADMIN ONLY) */}
      {isAdmin && (
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Users className="w-4 h-4 text-brand-500" />
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                  Institutional Member Accounts & Credentials
                </h2>
                <p className="text-[11px] text-slate-400">
                  New members are created exclusively by the Administrator. Provide them their assigned username to let them log in.
                </p>
              </div>
            </div>
            <button
              onClick={fetchUsers}
              disabled={loadingUsers}
              className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingUsers ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* Members Table */}
          <div className="overflow-x-auto rounded-2xl border border-slate-200/60 dark:border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-[10px] font-bold text-slate-500 uppercase">
                <tr>
                  <th className="px-4 py-3">Username</th>
                  <th className="px-4 py-3">Full Name</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3">Institutional Email</th>
                  <th className="px-4 py-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {systemUsers.map((u) => {
                  let roleColor = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
                  if (u.role === 'admin') roleColor = 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300';
                  else if (u.role === 'faculty') roleColor = 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300';
                  else if (u.role === 'coordinator') roleColor = 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300';
                  else if (u.role === 'club') roleColor = 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300';

                  return (
                    <tr key={u.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                      <td className="px-4 py-3 font-mono font-bold text-brand-600 dark:text-brand-400">
                        @{u.username}
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900 dark:text-slate-100">
                        <div>{u.name}</div>
                        {u.qualifications && u.qualifications.length > 0 && (
                          <div className="text-[10px] text-slate-500 font-normal">
                            🎓 {u.qualifications.join(', ')}
                          </div>
                        )}
                        {u.fields_of_interest && u.fields_of_interest.length > 0 && (
                          <div className="text-[10px] text-brand-600 dark:text-brand-400 font-normal">
                            ✨ {u.fields_of_interest.join(', ')}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${roleColor}`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                        {u.department} {u.faculty_id ? `(${u.faculty_id})` : ''}
                      </td>
                      <td className="px-4 py-3 text-slate-500">
                        {u.email}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 font-bold text-[10px]">
                          ACTIVE
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Solver Soft Objective Tuning */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 dark:border-slate-800 pb-3">
          <Sliders className="w-4 h-4 text-brand-500" />
          <h2 className="text-sm font-bold text-slate-900 dark:text-white">
            Soft Optimization Penalty Weights
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <div className="flex justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">
                Faculty Day-Spread Priority
              </span>
              <span className="font-bold text-brand-600 dark:text-brand-400">{spreadWeight}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={spreadWeight}
              onChange={(e) => setSpreadWeight(Number(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">
                Max Daily Load Cap
              </span>
              <span className="font-bold text-brand-600 dark:text-brand-400">{loadWeight}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={loadWeight}
              onChange={(e) => setLoadWeight(Number(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">
                Morning Hours Core Lecture Weight
              </span>
              <span className="font-bold text-brand-600 dark:text-brand-400">{morningWeight}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={morningWeight}
              onChange={(e) => setMorningWeight(Number(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">
                Student Gap Minimization
              </span>
              <span className="font-bold text-brand-600 dark:text-brand-400">{gapWeight}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={gapWeight}
              onChange={(e) => setGapWeight(Number(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>
        </div>
      </div>

      {/* Immutable Audit Trail */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <History className="w-4 h-4 text-emerald-500" />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              Institutional Audit Trail (Tamper-Resistant)
            </h2>
          </div>
          <button
            onClick={fetchLogs}
            disabled={loadingLogs}
            className="p-1 rounded-lg text-slate-400 hover:bg-slate-100"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingLogs ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
          {logs.map((log) => (
            <div
              key={log.id}
              className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2"
            >
              <div>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  {log.action}
                </span>
                <span className="text-slate-400 ml-2">by {log.user}</span>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 truncate max-w-xl">
                  {log.details}
                </p>
              </div>
              <span className="text-[10px] text-slate-400 shrink-0">{log.timestamp}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Danger Zone: Reset Demo Data */}
      <div className="p-6 rounded-3xl bg-rose-500/5 dark:bg-rose-950/20 border border-rose-500/20 space-y-3">
        <div className="flex items-center space-x-2 text-rose-600 dark:text-rose-400">
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <h2 className="text-sm font-bold">Restore Demo Dataset</h2>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Restore the entire system to initial baseline dataset with pre-generated timetable, exams, and verified demo accounts.
        </p>
        <button
          onClick={() => setShowResetModal(true)}
          className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs transition-colors flex items-center space-x-2"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Restore Pristine Demo State</span>
        </button>
      </div>

      {/* ADD MEMBER MODAL (ADMIN ONLY) */}
      {showAddUserModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                  <UserPlus className="w-5 h-5 text-brand-500" />
                  <span>Create Institutional Member Account</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Assign an authorized username & credentials to grant portal access
                </p>
              </div>
              <button
                onClick={() => setShowAddUserModal(false)}
                className="p-1.5 rounded-xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            {createdCredential ? (
              <div className="p-6 space-y-4">
                <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs space-y-2">
                  <div className="flex items-center space-x-2 font-bold text-sm">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <span>Member Created Successfully!</span>
                  </div>
                  <p>
                    Hand over these institutional credentials to <strong>{createdCredential.name}</strong>:
                  </p>
                  <div className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-emerald-200 dark:border-emerald-800 font-mono text-xs space-y-1">
                    <div><strong>Username:</strong> <span className="text-brand-600 dark:text-brand-400 font-bold">{createdCredential.username}</span></div>
                    <div><strong>Assigned Role:</strong> <span className="uppercase font-bold">{createdCredential.role}</span></div>
                    <div><strong>Password:</strong> <span className="text-slate-800 dark:text-slate-200">{createdCredential.password}</span></div>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    The member can now select their role on the login screen, enter their username, and immediately open their dedicated portal.
                  </p>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => {
                      setCreatedCredential(null);
                      setShowAddUserModal(false);
                    }}
                    className="px-4 py-2 text-xs font-bold text-white bg-brand-600 rounded-xl"
                  >
                    Done & Close
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleCreateUser} className="p-6 space-y-4">
                {createUserError && (
                  <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs">
                    {createUserError}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Member Role *
                    </label>
                    <select
                      value={newRole}
                      onChange={(e) => setNewRole(e.target.value as any)}
                      className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-semibold"
                    >
                      <option value="faculty">Faculty Member</option>
                      <option value="coordinator">Academic Coordinator</option>
                      <option value="club">Student Club Lead</option>
                      <option value="admin">System Administrator</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Department *
                    </label>
                    <select
                      value={newDept}
                      onChange={(e) => setNewDept(e.target.value)}
                      className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                    >
                      <option value="CSE">Computer Science & Eng (CSE)</option>
                      <option value="ECE">Electronics & Comm (ECE)</option>
                      <option value="ME">Mechanical Eng (ME)</option>
                      <option value="BS">Basic Sciences (BS)</option>
                      <option value="Student Council">Student Council / Clubs</option>
                      <option value="Dean's Office">Dean's Office</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Prof. Subhash Das"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Username (for Login) *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. prof_das"
                      value={newUsername}
                      onChange={(e) => setNewUsername(e.target.value)}
                      className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Initial Password *
                    </label>
                    <input
                      type="password"
                      required
                      placeholder="e.g. Das@Secure2026"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                    />
                  </div>
                </div>

                {newRole === 'faculty' && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Faculty ID (optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. F42"
                      value={newFacultyId}
                      onChange={(e) => setNewFacultyId(e.target.value)}
                      className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Academic Qualifications & Degrees (comma-separated)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Ph.D. in Computer Science (IIT Bombay), M.Tech in CSE"
                    value={newQualifications}
                    onChange={(e) => setNewQualifications(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  />
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Faculty will be automatically assigned to departmental lecture/lab sessions matching their qualifications.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Fields of Interest & Specialization (comma-separated)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Artificial Intelligence, Cloud Computing, Algorithms"
                    value={newFieldsOfInterest}
                    onChange={(e) => setNewFieldsOfInterest(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddUserModal(false)}
                    className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createUserLoading}
                    className="px-4 py-2 text-xs font-bold text-white bg-brand-600 hover:bg-brand-500 rounded-xl shadow-md transition-all flex items-center space-x-1.5"
                  >
                    {createUserLoading ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <UserPlus className="w-3.5 h-3.5" />
                    )}
                    <span>Create & Assign Credentials</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* RESET CONFIRMATION MODAL */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600 dark:text-rose-400">
              <AlertTriangle className="w-6 h-6 shrink-0" />
              <h3 className="text-base font-bold">Confirm Baseline Reset</h3>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              This action resets all dynamic venue bookings, manual overrides, and disruptions back to initial Gate A/B/C state. Type <strong>RESET</strong> to confirm.
            </p>
            <input
              type="text"
              value={resetInput}
              onChange={(e) => setResetInput(e.target.value)}
              placeholder="Type RESET"
              className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono"
            />
            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                onClick={() => setShowResetModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleResetConfirm}
                disabled={resetInput !== 'RESET' || resetting}
                className="px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 rounded-xl disabled:opacity-40"
              >
                {resetting ? 'Resetting...' : 'Confirm Reset'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
