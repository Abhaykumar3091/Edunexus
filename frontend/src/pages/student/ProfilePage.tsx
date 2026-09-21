import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/context/AuthContext';
import { User, Mail, Hash, ShieldCheck, Phone } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Student Profile</h1>
        <p className="text-sm text-slate-500">Verified academic enrollment records and security settings</p>
      </div>

      <Card>
        <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-slate-100">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-2xl bg-teal-600 text-white flex items-center justify-center font-bold text-2xl shadow-sm">
              {user?.full_name?.charAt(0) || 'S'}
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">{user?.full_name}</h2>
              <p className="text-sm text-slate-500">{user?.university_id || 'STU1001'} • Computer Science & Engineering</p>
            </div>
          </div>
          <Badge variant="success" className="mt-3 sm:mt-0">
            Enrolled & Active
          </Badge>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-100 bg-slate-50/50">
              <Mail className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-xs text-slate-400 font-medium">University Email</div>
                <div className="text-sm font-semibold text-slate-900">{user?.email}</div>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-100 bg-slate-50/50">
              <Hash className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-xs text-slate-400 font-medium">University ID</div>
                <div className="text-sm font-semibold text-slate-900">{user?.university_id || 'STU1001'}</div>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-100 bg-slate-50/50">
              <ShieldCheck className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-xs text-slate-400 font-medium">Role & Privileges</div>
                <div className="text-sm font-semibold text-slate-900">STUDENT (Standard Academic Access)</div>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-100 bg-slate-50/50">
              <Phone className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-xs text-slate-400 font-medium">Registered Phone</div>
                <div className="text-sm font-semibold text-slate-900">+1 (555) 392-1849</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
