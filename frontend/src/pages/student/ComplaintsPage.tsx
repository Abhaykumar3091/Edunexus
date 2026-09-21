import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { AlertCircle, Plus, Clock, CheckCircle2, RefreshCw, MessageSquare } from 'lucide-react';
import { studentService } from '@/services/student';
import { Complaint, ComplaintCategory } from '@/types/student';

export const ComplaintsPage: React.FC = () => {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [category, setCategory] = useState<ComplaintCategory>('HOSTEL');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchComplaints = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await studentService.getComplaints();
      if (res.success && res.data) {
        setComplaints(res.data);
      } else {
        setError(res.error?.message || 'Failed to fetch complaints');
      }
    } catch (e: any) {
      setError(e.message || 'Error connecting to backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;

    setSubmitting(true);
    try {
      const fullDescription = location.trim() ? `[Location: ${location.trim()}]\n${description}` : description;
      const res = await studentService.createComplaint({
        title,
        description: fullDescription,
        category,
      });

      if (res.success && res.data) {
        const newComplaint = res.data;
        setComplaints((prev) => [newComplaint, ...prev]);
        setShowModal(false);
        setTitle('');
        setDescription('');
        setLocation('');
      } else {
        alert(res.error?.message || 'Failed to submit grievance');
      }
    } catch (e: any) {
      alert(e.message || 'Error submitting complaint');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <Badge variant="secondary">OPEN</Badge>;
      case 'ASSIGNED':
        return <Badge variant="outline">ASSIGNED</Badge>;
      case 'IN_PROGRESS':
        return <Badge variant="warning">IN PROGRESS</Badge>;
      case 'RESOLVED':
        return <Badge variant="success">RESOLVED</Badge>;
      case 'CLOSED':
        return <Badge variant="secondary">CLOSED</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Student Grievance & Complaint Portal</h1>
          <p className="text-sm text-slate-500">Submit requests to university administration and track SLA resolution</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchComplaints} disabled={loading} className="gap-1">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
          <Button onClick={() => setShowModal(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            <span>Raise New Complaint</span>
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-400">Loading complaints...</div>
      ) : complaints.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center space-y-3">
            <CheckCircle2 className="h-10 w-10 text-emerald-500 mx-auto" />
            <h3 className="text-base font-semibold text-slate-800">No active grievances</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              You do not have any open or past tickets. If you encounter any infrastructure or academic issues, click "Raise New Complaint" above.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {complaints.map((c) => (
            <Card key={c.id} className="hover:border-slate-300 transition-colors">
              <CardContent className="p-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                      {c.ticket_id}
                    </span>
                    <span className="text-xs text-slate-300">•</span>
                    <span className="text-xs font-semibold text-slate-600">{c.category}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(c.status)}
                  </div>
                </div>

                <div>
                  <h3 className="text-base font-bold text-slate-900">{c.title}</h3>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">{c.description}</p>
                  {c.assigned_to && (
                    <p className="text-xs text-slate-500 mt-2">
                      Assigned Department: <span className="font-semibold text-slate-700">{c.assigned_to}</span>
                    </p>
                  )}
                </div>

                {c.resolution_notes && (
                  <div className="p-3 bg-emerald-50 rounded-lg text-xs text-emerald-800 border border-emerald-100">
                    <span className="font-semibold">Resolution Note: </span>
                    {c.resolution_notes}
                  </div>
                )}

                <div className="text-[11px] text-slate-400">
                  Logged: {new Date(c.created_at).toLocaleDateString()} at {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* New Complaint Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Raise Student Grievance / Complaint</h3>
              <p className="text-xs text-slate-500">
                Your ticket will be recorded in PostgreSQL and assigned to the relevant university department.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3">
              <Input
                label="Complaint Title"
                required
                placeholder="e.g. WiFi connectivity issue in Library Floor 2"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value as ComplaintCategory)}
                  className="w-full text-sm rounded-lg border border-slate-200 p-2 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                >
                  <option value="HOSTEL">Hostel & Accommodation</option>
                  <option value="ACADEMICS">Academic & Courses</option>
                  <option value="INFRASTRUCTURE">Library & Infrastructure</option>
                  <option value="FEES">Fees & Finance</option>
                  <option value="EXAMINATION">Examination Department</option>
                  <option value="OTHER">Other Issue</option>
                </select>
              </div>

              <Input
                label="Location / Room (Optional)"
                placeholder="e.g. Hostel Block B, Room 208"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Detailed Description</label>
                <textarea
                  required
                  rows={3}
                  className="w-full text-sm rounded-lg border border-slate-200 p-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  placeholder="Provide complete details regarding your issue..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Submit Grievance'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
