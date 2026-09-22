import React, { useState } from 'react';
import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom';
import {
  GraduationCap,
  LayoutDashboard,
  Clock,
  AlertCircle,
  User as UserIcon,
  LogOut,
  Menu,
  X,
  Sparkles,
  FileText,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

export const StudentLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { label: 'Dashboard', path: '/student/dashboard', icon: LayoutDashboard },
    { label: 'Ask UniAssist AI', path: '/student/chat', icon: Sparkles, highlight: true },
    { label: 'Doc Intelligence Q&A', path: '/student/document-ai', icon: FileText, highlight: true },
    { label: 'Profile', path: '/student/profile', icon: UserIcon },
  ];

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className="min-h-screen bg-emerald-50/40 flex flex-col md:flex-row">
      {/* Mobile Top Navbar */}
      <div className="md:hidden bg-white border-b border-emerald-100 px-4 py-3 flex items-center justify-between sticky top-0 z-30 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="bg-gradient-to-br from-teal-500 to-blue-600 text-white p-1.5 rounded-lg shadow-sm">
            <GraduationCap className="h-5 w-5" />
          </div>
          <span className="font-bold text-slate-800 tracking-tight">UniAssist AI</span>
        </div>
        <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="p-2 text-slate-600 hover:text-slate-900">
          {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`fixed md:sticky top-0 z-40 h-screen w-64 bg-white border-r border-emerald-100 flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 shadow-md ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
        {/* Brand */}
        <div className="p-5 border-b border-emerald-100 bg-gradient-to-r from-teal-50 to-blue-50">
          <Link to="/student/dashboard" className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-teal-500 to-blue-600 text-white p-2 rounded-xl shadow-sm">
              <GraduationCap className="h-6 w-6" />
            </div>
            <div>
              <div className="font-bold text-slate-800 leading-tight">UniAssist AI</div>
              <div className="text-xs text-teal-600 font-medium">Student Portal</div>
            </div>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-teal-600 to-blue-600 text-white shadow-sm'
                    : item.highlight
                    ? 'text-teal-700 hover:bg-teal-50 hover:text-teal-800'
                    : 'text-slate-600 hover:bg-emerald-50 hover:text-slate-900'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-white' : item.highlight ? 'text-teal-500' : 'text-slate-400'}`} />
                <span>{item.label}</span>
                {item.highlight && !isActive && (
                  <span className="ml-auto text-[10px] py-0 px-1.5 bg-teal-100 text-teal-700 rounded-md font-semibold">AI</span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User footer */}
        <div className="p-4 border-t border-emerald-100 bg-emerald-50/50">
          <div className="flex items-center gap-3 mb-3 p-2.5 rounded-xl bg-white border border-emerald-100 shadow-sm">
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-teal-400 to-blue-500 text-white flex items-center justify-center font-semibold text-sm shadow-sm">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'S'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-900 truncate">{user?.full_name || 'Student'}</p>
              <p className="text-xs text-slate-500 truncate">{user?.university_id || user?.email}</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={handleLogout} className="w-full justify-start gap-2 text-slate-600 hover:text-red-600 hover:border-red-200 hover:bg-red-50 border-emerald-200">
            <LogOut className="h-4 w-4" />
            <span>Sign Out</span>
          </Button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top header */}
        <header className="hidden md:flex h-16 bg-white/90 backdrop-blur-sm border-b border-emerald-100 px-8 items-center justify-between sticky top-0 z-20 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500 font-medium">Academic Year 2026-27</span>
            <span className="text-slate-300 mx-1">|</span>
            <Badge variant="success" className="text-xs">System Active</Badge>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-teal-400 to-blue-500 text-white flex items-center justify-center font-semibold text-xs shadow-sm">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'S'}
              </div>
              <div className="text-right">
                <p className="text-xs font-semibold text-slate-900 leading-tight">{user?.full_name}</p>
                <p className="text-[11px] text-slate-500">Student</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page body */}
        <main className="flex-1 p-4 md:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
