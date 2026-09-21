import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '@/services/auth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [universityId, setUniversityId] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);
    const res = await authService.register({
      full_name: fullName,
      email,
      university_id: universityId || undefined,
      password,
      role: 'STUDENT',
    });
    setLoading(false);

    if (res.success) {
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } else {
      setError(res.error?.message || 'Registration failed. Please check your information.');
    }
  };

  return (
    <div>
      <h3 className="text-xl font-bold text-slate-900 mb-1">Create Student Account</h3>
      <p className="text-sm text-slate-500 mb-6">Register your official student profile</p>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-sm text-emerald-700 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
          <span>Account created successfully! Redirecting to login...</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          id="fullName"
          label="Full Legal Name"
          required
          placeholder="Jordan Smith"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />

        <Input
          id="email"
          label="University Email"
          type="email"
          required
          placeholder="jordan.smith@university.edu"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <Input
          id="universityId"
          label="Student ID (Optional)"
          placeholder="STU1042"
          value={universityId}
          onChange={(e) => setUniversityId(e.target.value)}
        />

        <Input
          id="password"
          label="Password (min 8 characters)"
          type="password"
          required
          placeholder="••••••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <Input
          id="confirmPassword"
          label="Confirm Password"
          type="password"
          required
          placeholder="••••••••••••"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />

        <Button type="submit" className="w-full" isLoading={loading}>
          Create Account
        </Button>
      </form>

      <div className="mt-6 text-center text-xs text-slate-500">
        Already registered?{' '}
        <Link to="/login" className="font-semibold text-teal-600 hover:text-teal-700">
          Sign in here
        </Link>
      </div>
    </div>
  );
};
