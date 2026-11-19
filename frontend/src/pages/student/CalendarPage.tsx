import React, { useState } from 'react';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  AlertCircle,
  FileText,
  Bookmark,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { get } from '@/lib/api';
import { CalendarEvent } from '@/types';
import { formatDate, formatDateTime } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';

export const CalendarPage: React.FC = () => {
  const [currentDate, setCurrentDate] = useState(new Date(2026, 10, 19)); // Nov 2026
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  const { data: events = defaultEvents, isLoading } = useQuery({
    queryKey: ['academic_calendar_events'],
    queryFn: async (): Promise<CalendarEvent[]> => {
      try {
        return await get<CalendarEvent[]>('/calendar/events');
      } catch {
        return defaultEvents;
      }
    },
  });

  // Calendar math for November 2026
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  // Helper to filter events on a specific day
  const getEventsForDay = (day: number) => {
    const dayStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return events.filter((e) => e.start_datetime.startsWith(dayStr));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <CalendarIcon className="h-6 w-6 text-coglearn-600" />
            Academic Calendar
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Track assignment deadlines, exam sessions, and institutional events.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center rounded-lg border border-slate-200 bg-white shadow-xs p-1">
            <Button variant="ghost" size="sm" onClick={handlePrevMonth} className="px-2">
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="px-3 text-sm font-bold text-slate-800">
              {monthNames[month]} {year}
            </span>
            <Button variant="ghost" size="sm" onClick={handleNextMonth} className="px-2">
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <Card className="overflow-hidden">
        {/* Day Header */}
        <div className="grid grid-cols-7 border-b border-slate-200 bg-slate-50/80 text-center text-xs font-semibold text-slate-600 py-3">
          <span>Sun</span>
          <span>Mon</span>
          <span>Tue</span>
          <span>Wed</span>
          <span>Thu</span>
          <span>Fri</span>
          <span>Sat</span>
        </div>

        {/* Days cells */}
        <div className="grid grid-cols-7 auto-rows-fr divide-x divide-y divide-slate-100 bg-slate-100/40">
          {/* Empty pre-offset days */}
          {Array.from({ length: firstDay }).map((_, i) => (
            <div key={`empty-${i}`} className="min-h-[105px] bg-slate-50/50 p-2" />
          ))}

          {/* Month Days */}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1;
            const dayEvents = getEventsForDay(day);
            const isToday = day === 19 && month === 10 && year === 2026;

            return (
              <div
                key={`day-${day}`}
                className={`min-h-[110px] bg-white p-2 transition-colors hover:bg-slate-50/80 flex flex-col ${
                  isToday ? 'ring-2 ring-inset ring-coglearn-500 bg-coglearn-50/20' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span
                    className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${
                      isToday
                        ? 'bg-coglearn-600 text-white'
                        : 'text-slate-700'
                    }`}
                  >
                    {day}
                  </span>
                  {dayEvents.length > 0 && (
                    <span className="text-[10px] text-slate-400 font-mono">
                      {dayEvents.length} event{dayEvents.length > 1 ? 's' : ''}
                    </span>
                  )}
                </div>

                {/* Day events badges */}
                <div className="space-y-1 overflow-hidden flex-1">
                  {dayEvents.map((evt) => (
                    <button
                      key={evt.id}
                      onClick={() => setSelectedEvent(evt)}
                      className={`w-full text-left rounded p-1 text-[11px] font-medium truncate flex items-center gap-1 transition-all ${
                        evt.event_type === 'assessment'
                          ? 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200'
                          : evt.event_type === 'quiz'
                          ? 'bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200'
                          : evt.event_type === 'assignment'
                          ? 'bg-sky-50 text-sky-700 hover:bg-sky-100 border border-sky-200'
                          : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                      }`}
                    >
                      <span className="truncate">{evt.title}</span>
                      {evt.is_revised && (
                        <span className="ml-auto text-[9px] font-bold text-amber-600 shrink-0">
                          REV
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Revised Deadlines Note */}
      <div className="flex items-center gap-4 text-xs text-slate-500 bg-white p-4 rounded-xl border border-slate-200">
        <span className="font-semibold text-slate-700">Legend:</span>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded bg-sky-200" />
          <span>Assignment Due</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded bg-amber-200" />
          <span>Quiz Due</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded bg-red-200" />
          <span>Major Assessment</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded bg-emerald-200" />
          <span>Institutional Event</span>
        </div>
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onClose={() => setSelectedEvent(null)}
          title={selectedEvent.title}
          description={`Event Type: ${selectedEvent.event_type.toUpperCase()}`}
          footer={
            <Button variant="outline" size="sm" onClick={() => setSelectedEvent(null)}>
              Close
            </Button>
          }
        >
          <div className="space-y-4 text-sm">
            {selectedEvent.is_revised && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-amber-800 text-xs flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
                <div>
                  <span className="font-bold">Deadline Revised by Academic Faculty</span>
                  <p className="mt-0.5">
                    Original due datetime:{' '}
                    <span className="line-through font-mono">
                      {formatDateTime(selectedEvent.original_datetime)}
                    </span>
                  </p>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Scheduled Date:</span>
                <span className="font-semibold text-slate-800">
                  {formatDateTime(selectedEvent.start_datetime)}
                </span>
              </div>
              {selectedEvent.end_datetime && (
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Closing Time:</span>
                  <span className="font-semibold text-slate-800">
                    {formatDateTime(selectedEvent.end_datetime)}
                  </span>
                </div>
              )}
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Classification:</span>
                <Badge variant="default" size="sm">
                  {selectedEvent.event_type}
                </Badge>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

// Fallback demo calendar events
const defaultEvents: CalendarEvent[] = [
  {
    id: 'evt-1',
    event_type: 'assignment',
    title: 'NP-Completeness Due',
    start_datetime: '2026-11-18T23:59:00Z',
    end_datetime: '2026-11-18T23:59:00Z',
    is_revised: false,
    original_datetime: null,
    source_task_id: 'task-4',
  },
  {
    id: 'evt-2',
    event_type: 'quiz',
    title: 'Distributed Systems Raft Quiz',
    start_datetime: '2026-11-20T18:00:00Z',
    end_datetime: '2026-11-20T19:00:00Z',
    is_revised: false,
    original_datetime: null,
    source_task_id: 'task-2',
  },
  {
    id: 'evt-3',
    event_type: 'assignment',
    title: 'Dynamic Programming Due (Revised)',
    start_datetime: '2026-11-21T23:59:00Z',
    end_datetime: '2026-11-21T23:59:00Z',
    is_revised: true,
    original_datetime: '2026-11-19T23:59:00Z',
    source_task_id: 'task-1',
  },
  {
    id: 'evt-4',
    event_type: 'assessment',
    title: 'Probability Midterm Assessment',
    start_datetime: '2026-11-25T14:00:00Z',
    end_datetime: '2026-11-25T16:00:00Z',
    is_revised: false,
    original_datetime: null,
    source_task_id: 'task-3',
  },
  {
    id: 'evt-5',
    event_type: 'institutional',
    title: 'Faculty Reading Day & Seminar',
    start_datetime: '2026-11-27T09:00:00Z',
    end_datetime: '2026-11-27T17:00:00Z',
    is_revised: false,
    original_datetime: null,
    source_task_id: null,
  },
];

export default CalendarPage;
