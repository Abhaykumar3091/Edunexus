import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { GraduationCap, ShieldCheck } from 'lucide-react';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link to="/" className="inline-flex items-center gap-3 justify-center mb-4">
          <div className="bg-blue-600 text-white p-2.5 rounded-2xl shadow-md">
            <GraduationCap className="h-7 w-7" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-slate-900">UniAssist AI</span>
        </Link>
        <h2 className="text-xl font-semibold tracking-tight text-slate-900">
          University AI Support Platform
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Official academic portal powered by Microsoft Azure
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-2xl sm:px-10">
          <Outlet />
        </div>

        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-400">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          <span>Role-based access control & Argon2id encrypted</span>
        </div>
      </div>
    </div>
  );
};
