import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent } from '@/components/ui/Card';
import {
  GraduationCap,
  Sparkles,
  ShieldCheck,
  Search,
  Database,
  Calendar,
  CreditCard,
  FileCheck,
  ArrowRight,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-teal-600 text-white p-2 rounded-xl shadow-sm">
              <GraduationCap className="h-6 w-6" />
            </div>
            <div>
              <span className="text-xl font-bold text-slate-900 tracking-tight">UniAssist AI</span>
              <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                Azure AI Powered
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
              Sign In
            </Button>
            <Button size="sm" onClick={() => navigate('/register')} className="shadow-sm">
              Register Student
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-16 md:py-24 bg-gradient-to-b from-white via-blue-50/20 to-slate-50 border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-100 text-blue-800 text-xs font-semibold">
            <Sparkles className="h-3.5 w-3.5 text-teal-600" />
            <span>Next-Generation University Intelligence Platform</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Accurate, Grounded Answers for <br className="hidden sm:inline" />
            <span className="text-teal-600">Every University Student.</span>
          </h1>

          <p className="max-w-2xl mx-auto text-base sm:text-lg text-slate-600 leading-relaxed">
            UniAssist AI connects students directly to official university regulations, timetable schedules and grievances through Microsoft Azure AI Foundry and Azure AI Search.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Button size="lg" onClick={() => navigate('/login')} className="w-full sm:w-auto gap-2 shadow-md">
              <span>Open Student Portal</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate('/login')} className="w-full sm:w-auto">
              Administrator Console
            </Button>
          </div>

          {/* Trust points */}
          <div className="pt-8 flex flex-wrap items-center justify-center gap-6 text-xs font-medium text-slate-500">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              Role-Based Access Control
            </span>
            <span className="flex items-center gap-1.5">
              <FileCheck className="h-4 w-4 text-teal-600" />
              Official Source Citations
            </span>
            <span className="flex items-center gap-1.5">
              <Database className="h-4 w-4 text-indigo-600" />
              Argon2id Encrypted Security
            </span>
          </div>
        </div>
      </section>

      {/* Feature Architecture Cards */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Built for Academic Rigor & Accuracy</h2>
          <p className="text-sm text-slate-500 max-w-xl mx-auto">
            A hybrid AI architecture uniting grounded document retrieval with secure transactional student database tools.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-slate-200 hover:border-teal-300 transition-colors shadow-sm">
            <CardContent className="p-6 space-y-3">
              <div className="h-11 w-11 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
                <Search className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Foundry IQ / Azure AI Search RAG</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Indexes academic calendars, library regulations, hostel rules, and policies. Answers include strict citations from official documents.
              </p>
            </CardContent>
          </Card>

          <Card className="border-slate-200 hover:border-teal-300 transition-colors shadow-sm">
            <CardContent className="p-6 space-y-3">
              <div className="h-11 w-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <Database className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Student Tool Calling</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Dynamic query routing to personal timetable and grievance tracking without cross-student data leakage.
              </p>
            </CardContent>
          </Card>

          <Card className="border-slate-200 hover:border-teal-300 transition-colors shadow-sm">
            <CardContent className="p-6 space-y-3">
              <div className="h-11 w-11 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Zero Hallucination Guardrails</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                If information cannot be verified in the university knowledge base, the agent transparently guides students to the relevant department.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto bg-white border-t border-slate-200 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© 2026 UniAssist AI • University Academic Support System</p>
          <div className="flex items-center gap-6">
            <span>Microsoft Azure AI Foundry</span>
            <span>Azure Container Apps</span>
            <span>PostgreSQL</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
