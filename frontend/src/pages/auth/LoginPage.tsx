import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { AlertCircle } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const result = await login(email, password);
    setLoading(false);

    if (result.success) {
      // Check stored user role to route appropriately
      const stored = localStorage.getItem('uniassist_user');
      if (stored) {
        try {
          const userObj = JSON.parse(stored);
          if (userObj.role === 'ADMIN') {
            navigate('/admin/dashboard');
            return;
          }
        } catch {
          // fallback
        }
      }
      navigate('/student/dashboard');
    } else {
      setError(result.message || 'Authentication failed. Please verify credentials.');
    }
  };

  const handleQuickLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div>
      <h3 className="text-xl font-bold text-slate-900 mb-1">Sign in to your account</h3>
      <p className="text-sm text-slate-500 mb-6">Enter your university credentials to continue</p>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          id="email"
          label="University Email"
          type="email"
          required
          placeholder="student@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <Input
          id="password"
          label="Password"
          type="password"
          required
          placeholder="••••••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <Button type="submit" className="w-full" isLoading={loading}>
          Sign In
        </Button>
      </form>

      {/* Quick Switch Demo Accounts */}
      <div className="mt-8 pt-6 border-t border-slate-200">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 text-center">
          Quick Demo Credentials
        </p>
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => handleQuickLogin('student@example.com', 'StudentPassword123!')}
            className="px-2 py-1.5 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 text-center transition-colors"
          >
            Student
          </button>
          <button
            type="button"
            onClick={() => handleQuickLogin('faculty@example.com', 'FacultyPassword123!')}
            className="px-2 py-1.5 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 text-center transition-colors"
          >
            Faculty
          </button>
          <button
            type="button"
            onClick={() => handleQuickLogin('admin@example.com', 'AdminPassword123!')}
            className="px-2 py-1.5 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 text-center transition-colors"
          >
            Admin
          </button>
        </div>
      </div>

      <div className="mt-6 text-center text-xs text-slate-500">
        New student?{' '}
        <Link to="/register" className="font-semibold text-teal-600 hover:text-teal-700">
          Create student account
        </Link>
      </div>
    </div>
  );
};
