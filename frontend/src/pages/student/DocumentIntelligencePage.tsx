import React, { useState, useRef, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  FileText, UploadCloud, Sparkles, Send, Bot, User as UserIcon,
  CheckCircle2, AlertCircle, FileCheck, RotateCcw, BookOpen, Layers,
  HelpCircle, Clock, ChevronRight, Database, ExternalLink, ShieldCheck, ListFilter,
} from "lucide-react";
import { documentService, AnalyzedDocument, DocumentCitation, RagUploadResult } from "@/services/documents";

interface QAMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: DocumentCitation[];
  timestamp: string;
}

export const DocumentIntelligencePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"rag_upload" | "instant_qa">("rag_upload");

  const [ragFile, setRagFile] = useState<File | null>(null);
  const [category, setCategory] = useState<string>("policy");
  const [ragUploading, setRagUploading] = useState(false);
  const [ragResult, setRagResult] = useState<RagUploadResult | null>(null);
  const [ragError, setRagError] = useState<string | null>(null);
  const [ragDocs, setRagDocs] = useState<any[]>([]);

  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzedDoc, setAnalyzedDoc] = useState<AnalyzedDocument | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<QAMessage[]>([]);
  const [asking, setAsking] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const ragFileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { fetchRagDocuments(); }, []);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const fetchRagDocuments = async () => {
    const res = await documentService.listRagDocuments();
    if (res.success && res.data) setRagDocs(res.data);
  };

  const handleRagFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setRagFile(e.target.files[0]);
      setRagError(null);
      setRagResult(null);
    }
  };

  const handleRagUpload = async () => {
    if (!ragFile) return;
    setRagUploading(true);
    setRagError(null);
    setRagResult(null);
    const res = await documentService.uploadForRag(ragFile, category);
    setRagUploading(false);
    if (res.success && res.data) {
      setRagResult(res.data);
      setRagFile(null);
      if (ragFileInputRef.current) ragFileInputRef.current.value = "";
      fetchRagDocuments();
    } else {
      setRagError(res.error?.message || "Failed to upload to Azure Blob Storage.");
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) { setFile(e.target.files[0]); setError(null); }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setAnalyzing(true);
    setError(null);
    const res = await documentService.uploadAndAnalyze(file);
    setAnalyzing(false);
    if (res.success && res.data) {
      setAnalyzedDoc(res.data);
      setMessages([{ id: "1", role: "assistant", content: "Document analyzed! Ask me anything about this file.", timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }]);
    } else {
      setError(res.error?.message || "Failed to analyze document.");
    }
  };

  const handleAskQuestion = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!question.trim() || !analyzedDoc || asking) return;
    const userQ = question.trim();
    setQuestion("");
    const userMsg: QAMessage = { id: Date.now().toString(), role: "user", content: userQ, timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) };
    setMessages((prev) => [...prev, userMsg]);
    setAsking(true);
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    const res = await documentService.askQuestion(analyzedDoc.document_id, userQ, history);
    setAsking(false);
    if (res.success && res.data) {
      setMessages((prev) => [...prev, { id: (Date.now() + 1).toString(), role: "assistant", content: res.data!.answer, citations: res.data!.citations, timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }]);
    } else {
      setMessages((prev) => [...prev, { id: (Date.now() + 1).toString(), role: "assistant", content: "Sorry, I could not get an answer. Please try again.", timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }]);
    }
  };

  const categoryOptions = [
    { value: "policy", label: "Policy Document" },
    { value: "syllabus", label: "Syllabus" },
    { value: "circular", label: "Circular / Notice" },
    { value: "academic", label: "Academic Resource" },
    { value: "exam", label: "Exam Related" },
    { value: "other", label: "Other" },
  ];

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white/60 dark:bg-slate-900/60 backdrop-blur-xl p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="secondary" className="bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 border-indigo-200/50">
              <Database className="w-3 h-3 mr-1" /> Azure Blob Storage & RAG Pipeline
            </Badge>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Knowledge Base & Document Intelligence</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Upload PDFs to Azure Blob Storage for university-wide RAG AI Chat, or analyze files for instant Q&A.</p>
        </div>
        <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl self-start md:self-auto">
          <button onClick={() => setActiveTab("rag_upload")} className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all flex items-center gap-2 ${activeTab === "rag_upload" ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"}`}>
            <UploadCloud className="w-4 h-4" /> Azure RAG Storage
          </button>
          <button onClick={() => setActiveTab("instant_qa")} className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all flex items-center gap-2 ${activeTab === "instant_qa" ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"}`}>
            <Sparkles className="w-4 h-4" /> Instant Q&A
          </button>
        </div>
      </div>

      {activeTab === "rag_upload" && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card className="border-slate-200/80 dark:border-slate-800/80 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base"><UploadCloud className="w-5 h-5 text-indigo-500" /> Upload to Azure Blob</CardTitle>
                <CardDescription>Documents become available for AI-powered Q&A across the university.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div onClick={() => ragFileInputRef.current?.click()} className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-6 text-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50/40 dark:hover:bg-indigo-950/20 transition-all group">
                  <input ref={ragFileInputRef} type="file" accept=".pdf,.doc,.docx,.txt,.pptx" className="hidden" onChange={handleRagFileSelect} />
                  <UploadCloud className="w-8 h-8 mx-auto text-slate-400 group-hover:text-indigo-500 transition-colors mb-2" />
                  {ragFile ? (
                    <div><p className="text-sm font-semibold text-slate-700 dark:text-slate-300">{ragFile.name}</p><p className="text-xs text-slate-500 mt-0.5">{(ragFile.size / 1024).toFixed(1)} KB</p></div>
                  ) : (
                    <div><p className="text-sm text-slate-600 dark:text-slate-400">Click to select a file</p><p className="text-xs text-slate-400 dark:text-slate-500 mt-1">PDF, DOCX, PPTX, TXT supported</p></div>
                  )}
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">Document Category</label>
                  <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    {categoryOptions.map((opt) => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
                  </select>
                </div>
                <Button onClick={handleRagUpload} disabled={!ragFile || ragUploading} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
                  {ragUploading ? <span className="flex items-center gap-2"><svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>Uploading to Azure...</span> : <span className="flex items-center gap-2"><UploadCloud className="w-4 h-4" />Upload to Blob Storage</span>}
                </Button>
                {ragResult && (
                  <div className="rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/50 p-4 space-y-2">
                    <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 font-semibold text-sm"><CheckCircle2 className="w-4 h-4" /> Uploaded Successfully</div>
                    <p className="text-xs text-emerald-600 dark:text-emerald-500 break-all">Blob: <span className="font-mono">{ragResult.blob_name}</span></p>
                    <p className="text-xs text-emerald-600 dark:text-emerald-500">Container: <span className="font-semibold">{ragResult.rag_container}</span></p>
                    <p className="text-xs text-emerald-600 dark:text-emerald-500">Size: {(ragResult.size_bytes / 1024).toFixed(1)} KB</p>
                    {ragResult.rag_ready && <Badge className="bg-emerald-100 text-emerald-700 border-emerald-300 text-xs"><ShieldCheck className="w-3 h-3 mr-1" /> RAG Ready</Badge>}
                  </div>
                )}
                {ragError && (
                  <div className="rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 p-4 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-red-600 dark:text-red-400">{ragError}</p>
                  </div>
                )}
              </CardContent>
            </Card>
            <Card className="border-slate-200/80 dark:border-slate-800/80 shadow-sm bg-indigo-50/50 dark:bg-indigo-950/20">
              <CardContent className="p-4 space-y-3">
                <p className="text-xs font-bold text-indigo-700 dark:text-indigo-400 uppercase tracking-wider">How RAG Works</p>
                {[{ icon: UploadCloud, text: "You upload a document (PDF, DOCX, etc.)" }, { icon: Database, text: "It gets stored in Azure Blob Storage with metadata" }, { icon: Sparkles, text: "AI indexes it and makes it searchable" }, { icon: HelpCircle, text: "Any user can ask questions — AI finds answers from stored docs" }].map(({ icon: Icon, text }, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    <div className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center flex-shrink-0"><Icon className="w-3 h-3 text-indigo-600 dark:text-indigo-400" /></div>
                    <p className="text-xs text-indigo-700 dark:text-indigo-300">{text}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
          <div className="lg:col-span-3">
            <Card className="border-slate-200/80 dark:border-slate-800/80 shadow-sm h-full">
              <CardHeader className="border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base"><ListFilter className="w-5 h-5 text-indigo-500" /> Azure Blob Library</CardTitle>
                  <button onClick={fetchRagDocuments} className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"><RotateCcw className="w-3 h-3" /> Refresh</button>
                </div>
                <CardDescription>All documents currently stored in Azure Blob Storage for RAG.</CardDescription>
              </CardHeader>
              <CardContent className="p-4">
                {ragDocs.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center"><Database className="w-10 h-10 text-slate-300 dark:text-slate-600 mb-3" /><p className="text-sm font-medium text-slate-500 dark:text-slate-400">No documents uploaded yet</p><p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Upload your first document to get started</p></div>
                ) : (
                  <div className="space-y-2">
                    {ragDocs.map((doc: any, i: number) => (
                      <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors">
                        <div className="w-9 h-9 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center flex-shrink-0"><FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /></div>
                        <div className="flex-1 min-w-0"><p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{doc.name || doc.blob_name || `Document ${i + 1}`}</p><p className="text-xs text-slate-400 dark:text-slate-500">{doc.size ? `${(doc.size / 1024).toFixed(1)} KB` : ""}{doc.last_modified ? ` · ${new Date(doc.last_modified).toLocaleDateString()}` : ""}</p></div>
                        <Badge variant="secondary" className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400">RAG</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {activeTab === "instant_qa" && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card className="border-slate-200/80 dark:border-slate-800/80 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base"><FileText className="w-5 h-5 text-violet-500" /> Analyze a Document</CardTitle>
                <CardDescription>Upload any file. Azure Document Intelligence will extract and index its content for Q&A.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div onClick={() => fileInputRef.current?.click()} className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-6 text-center cursor-pointer hover:border-violet-400 hover:bg-violet-50/40 dark:hover:bg-violet-950/20 transition-all group">
                  <input ref={fileInputRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.docx,.txt" className="hidden" onChange={handleFileSelect} />
                  <FileText className="w-8 h-8 mx-auto text-slate-400 group-hover:text-violet-500 transition-colors mb-2" />
                  {file ? (<div><p className="text-sm font-semibold text-slate-700 dark:text-slate-300">{file.name}</p><p className="text-xs text-slate-500 mt-0.5">{(file.size / 1024).toFixed(1)} KB</p></div>) : (<div><p className="text-sm text-slate-600 dark:text-slate-400">Click to select a file</p><p className="text-xs text-slate-400 dark:text-slate-500 mt-1">PDF, Image, DOCX, TXT</p></div>)}
                </div>
                <Button onClick={handleAnalyze} disabled={!file || analyzing} className="w-full bg-violet-600 hover:bg-violet-700 text-white">
                  {analyzing ? <span className="flex items-center gap-2"><svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>Analyzing with Azure...</span> : <span className="flex items-center gap-2"><Sparkles className="w-4 h-4" />Analyze Document</span>}
                </Button>
                {error && (<div className="rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 p-4 flex items-start gap-2"><AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" /><p className="text-xs text-red-600 dark:text-red-400">{error}</p></div>)}
                {analyzedDoc && (
                  <div className="rounded-xl bg-violet-50 dark:bg-violet-950/30 border border-violet-200 dark:border-violet-800/50 p-4 space-y-2">
                    <p className="text-xs font-bold text-violet-700 dark:text-violet-400 uppercase tracking-wider flex items-center gap-1"><FileCheck className="w-3.5 h-3.5" /> Document Ready</p>
                    <p className="text-xs text-violet-600 dark:text-violet-400 font-medium truncate">{analyzedDoc.filename}</p>
                    <div className="flex gap-3 text-xs text-violet-500"><span className="flex items-center gap-1"><BookOpen className="w-3 h-3" />{analyzedDoc.page_count} pages</span><span className="flex items-center gap-1"><Layers className="w-3 h-3" />{analyzedDoc.sections?.length || 0} sections</span></div>
                    {analyzedDoc.summary_preview && <p className="text-xs text-violet-600 dark:text-violet-400 line-clamp-3 mt-1">{analyzedDoc.summary_preview}</p>}
                    <button onClick={() => { setFile(null); setAnalyzedDoc(null); setMessages([]); setError(null); }} className="text-xs text-slate-500 hover:text-red-500 flex items-center gap-1 mt-1 transition-colors"><RotateCcw className="w-3 h-3" /> Reset</button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
          <div className="lg:col-span-3">
            <Card className="border-slate-200/80 dark:border-slate-800/80 shadow-sm flex flex-col h-[600px]">
              <CardHeader className="border-b border-slate-100 dark:border-slate-800 flex-shrink-0">
                <CardTitle className="flex items-center gap-2 text-base"><Bot className="w-5 h-5 text-violet-500" /> Document Q&A Chat</CardTitle>
                <CardDescription>{analyzedDoc ? `Asking questions about: ${analyzedDoc.filename}` : "Analyze a document on the left to start chatting."}</CardDescription>
              </CardHeader>
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && !analyzedDoc && (<div className="flex flex-col items-center justify-center h-full text-center"><Bot className="w-12 h-12 text-slate-300 dark:text-slate-600 mb-3" /><p className="text-sm font-medium text-slate-500 dark:text-slate-400">No document loaded</p><p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Upload and analyze a document to start Q&A</p></div>)}
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    {msg.role === "assistant" && (<div className="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-900/50 flex items-center justify-center flex-shrink-0 mt-0.5"><Bot className="w-4 h-4 text-violet-600 dark:text-violet-400" /></div>)}
                    <div className={`max-w-[80%] space-y-1 ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
                      <div className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${msg.role === "user" ? "bg-violet-600 text-white rounded-br-sm" : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-sm"}`}>{msg.content}</div>
                      {msg.citations && msg.citations.length > 0 && (<div className="space-y-1 w-full">{msg.citations.map((c, ci) => (<div key={ci} className="text-xs bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 rounded-lg px-3 py-1.5 text-amber-700 dark:text-amber-400"><span className="font-semibold">Source:</span> {c.source_file} — "{c.snippet}"</div>))}</div>)}
                      <span className="text-xs text-slate-400 dark:text-slate-500 px-1">{msg.timestamp}</span>
                    </div>
                    {msg.role === "user" && (<div className="w-8 h-8 rounded-full bg-violet-600 flex items-center justify-center flex-shrink-0 mt-0.5"><UserIcon className="w-4 h-4 text-white" /></div>)}
                  </div>
                ))}
                {asking && (<div className="flex gap-3 justify-start"><div className="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-900/50 flex items-center justify-center flex-shrink-0"><Bot className="w-4 h-4 text-violet-600 dark:text-violet-400" /></div><div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-slate-100 dark:bg-slate-800"><div className="flex gap-1 items-center"><span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "0ms" }} /><span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "150ms" }} /><span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "300ms" }} /></div></div></div>)}
                <div ref={chatEndRef} />
              </div>
              <div className="border-t border-slate-100 dark:border-slate-800 p-4 flex-shrink-0">
                <form onSubmit={handleAskQuestion} className="flex gap-2">
                  <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder={analyzedDoc ? "Ask a question about the document..." : "Analyze a document first..."} disabled={!analyzedDoc || asking} className="flex-1 text-sm px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50" />
                  <Button type="submit" disabled={!analyzedDoc || asking || !question.trim()} className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2.5 rounded-xl"><Send className="w-4 h-4" /></Button>
                </form>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentIntelligencePage;
