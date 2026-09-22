import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  Sparkles, ArrowRight, Bell,
  CheckCircle2, FileText, MessageSquare, ShieldCheck, Database,
} from 'lucide-react';

export const StudentDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const studentName = user?.full_name ? user.full_name.split(' ')[0] : 'Student';
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Welcome Hero Banner */}
      <div className="bg-gradient-to-r from-teal-600 via-teal-500 to-blue-600 rounded-2xl p-6 md:p-8 text-white shadow-lg shadow-teal-100 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/15 text-xs font-medium text-teal-100 mb-3 border border-white/20">
            <Sparkles className="h-3.5 w-3.5 text-teal-100" />
            <span>Official University Student Portal</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">{greeting}, {studentName} 👋</h1>
          <p className="text-teal-100 mt-1.5 text-sm md:text-base max-w-xl">
            Welcome to your academic cockpit. Ask questions to UniAssist AI, analyze course documents with Document Intelligence, and access university knowledge resources.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <Button
            onClick={() => navigate('/student/chat')}
            className="bg-white text-teal-800 hover:bg-teal-50 font-semibold shadow-sm w-full md:w-auto border-0"
          >
            <Sparkles className="h-4 w-4 mr-2 text-teal-600" /> Ask UniAssist AI
          </Button>
          <Button
            onClick={() => navigate('/student/document-ai')}
            className="bg-teal-700/80 hover:bg-teal-800 text-white border border-teal-300/40 font-medium shadow-sm w-full md:w-auto"
          >
            <FileText className="h-4 w-4 mr-2 text-teal-200" /> Doc Intelligence
          </Button>
        </div>
      </div>

      {/* Main Highlights Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card
          className="border-teal-100 bg-gradient-to-br from-teal-50 to-white hover:shadow-md hover:border-teal-200 transition-all cursor-pointer"
          onClick={() => navigate('/student/chat')}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">UniAssist AI Assistant</CardTitle>
            <div className="p-2 bg-teal-100 text-teal-600 rounded-xl">
              <Sparkles className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">Online</div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="success" className="text-[10px] px-1.5 py-0">Zero-Hallucination Active</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-2">Grounded in official regulations</p>
          </CardContent>
        </Card>

        <Card
          className="border-sky-100 bg-gradient-to-br from-sky-50 to-white hover:shadow-md hover:border-sky-200 transition-all cursor-pointer"
          onClick={() => navigate('/student/document-ai')}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Document Intelligence</CardTitle>
            <div className="p-2 bg-sky-100 text-sky-600 rounded-xl">
              <FileText className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">AI Q&A</div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="default" className="text-[10px] px-1.5 py-0 bg-sky-600">Azure OCR</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-2">Upload PDFs and get grounded answers</p>
          </CardContent>
        </Card>

        <Card
          className="border-blue-100 bg-gradient-to-br from-blue-50 to-white hover:shadow-md hover:border-blue-200 transition-all cursor-pointer"
          onClick={() => navigate('/student/chat')}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">RAG Knowledge Base</CardTitle>
            <div className="p-2 bg-blue-100 text-blue-600 rounded-xl">
              <Database className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">Indexed</div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="success" className="text-[10px] px-1.5 py-0">
                Azure AI Search
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-2">Blob Storage & Search connected</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid: Feature Cards & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-teal-600" /> University AI Services
                </CardTitle>
                <CardDescription>Instant answers and document analysis powered by Azure AI</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              <div
                onClick={() => navigate('/student/chat')}
                className="flex items-center justify-between p-4 rounded-xl border border-teal-100 bg-teal-50/50 hover:bg-teal-50 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-sm shadow-sm group-hover:scale-105 transition-transform">
                    <MessageSquare className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">Ask University Regulations & Policies</h4>
                    <p className="text-xs text-slate-500">Hostel rules, fee structures, examination ordinances, and scholarships.</p>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-teal-600 group-hover:translate-x-1 transition-transform" />
              </div>

              <div
                onClick={() => navigate('/student/document-ai')}
                className="flex items-center justify-between p-4 rounded-xl border border-sky-100 bg-sky-50/50 hover:bg-sky-50 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-sky-600 text-white flex items-center justify-center font-bold text-sm shadow-sm group-hover:scale-105 transition-transform">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">Custom Document Intelligence Q&A</h4>
                    <p className="text-xs text-slate-500">Upload syllabus, assignment briefs, or study materials for instant breakdown.</p>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-sky-600 group-hover:translate-x-1 transition-transform" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right column alerts */}
        <div className="space-y-4">
          <Card className="border-emerald-100 bg-gradient-to-b from-emerald-50/60 to-white shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Bell className="h-4 w-4 text-emerald-600" />
                  Academic Alerts
                </CardTitle>
                <span className="text-xs text-slate-400 font-medium">Live</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="p-2.5 rounded-xl border border-teal-100 bg-teal-50/60 text-xs">
                <div className="font-semibold text-slate-900">Document Intelligence Active</div>
                <div className="text-slate-500 mt-0.5">Upload notes, PDFs, or regulations for instant AI analysis.</div>
                <div className="text-[10px] text-teal-600 font-semibold mt-1">Available</div>
              </div>
              <div className="p-2.5 rounded-xl border border-blue-100 bg-blue-50/50 text-xs">
                <div className="font-semibold text-slate-900">Zero-Hallucination Policy</div>
                <div className="text-slate-500 mt-0.5">All assistant responses are verified against Azure AI Search indexes.</div>
                <div className="text-[10px] text-blue-600 font-semibold mt-1">System Guard</div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-teal-100 bg-gradient-to-b from-teal-50/40 to-white shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-teal-600" /> Quick Questions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <button
                onClick={() => navigate('/student/chat')}
                className="w-full text-left p-2.5 rounded-xl border border-teal-100 bg-white hover:border-teal-300 hover:bg-teal-50/50 transition-all cursor-pointer"
              >
                <p className="text-xs font-medium text-slate-900">"What are the hostel silence hours?"</p>
                <p className="text-[10px] text-teal-600 mt-0.5 flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> Grounded in official University SOPs
                </p>
              </button>
              <button
                onClick={() => navigate('/student/chat')}
                className="w-full text-left p-2.5 rounded-xl border border-blue-100 bg-white hover:border-blue-300 hover:bg-blue-50/50 transition-all cursor-pointer"
              >
                <p className="text-xs font-medium text-blue-900">"What is the fee structure for MBA 2026?"</p>
                <p className="text-[10px] text-blue-600 mt-0.5">Fee & Scholarship rules</p>
              </button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
