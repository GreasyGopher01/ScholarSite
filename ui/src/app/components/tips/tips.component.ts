// tips.component.ts - Minimal Chrome-Safe Version
import { Component, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

interface Tip {
  title: string;
  description: string;
  points: string[];
  colorClass: string;
}

@Component({
  selector: 'app-tips',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './tips.component.html',
  styleUrls: ['./tips.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush // CRITICAL: Prevents excessive change detection
})
export class TipsComponent {
  // Use readonly to prevent accidental mutations
  readonly tips: Tip[] = [
    {
      title: 'Write A Standout Essay',
      description: 'Emphasize clear structure (hook → context → impact → reflection), authenticity, and specificity that differentiates the applicant.',
      points: [
        'Lead with a vivid hook that shows who you are.',
        'Focus on 1-2 defining experiences; avoid a resume recap.',
        'Show impact with numbers or concrete outcomes where possible.',
        'Reflect: what did you learn and how did it change your goals?',
        'Edit constantly read aloud; ask 1-2 trusted reviewers for feedback.',
        'Make sure your essay aligns with what the prompt asks for!'
      ],
      colorClass: 'blue'
    },
    {
      title: 'Demonstrate Genuine Passion',
      description: 'Explain how consistent commitments over time, self-driven projects, and leadership roles signal real interest.',
      points: [
        'Highlight multi-year involvement or increasing responsibility.',
        'Showcase self-started projects, competitions, or community impact.',
        'Connect your passion to the scholarship\'s mission and values.'
      ],
      colorClass: 'purple'
    },
    {
      title: 'Maintain Strong Academics',
      description: 'Stress course rigor, upward trends, and how applicants challenge themselves.',
      points: [
        'Take challenging courses when available; explain context if access is limited.',
        'Note GPA trends and improvements.',
        'Tie academics to skills used in projects, research, or service.'
      ],
      colorClass: 'green'
    },
    {
      title: 'Strong Letters of Recommendation',
      description: 'Explain choosing recommenders who know YOU well and can speak to character, growth, and impact.',
      points: [
        'Ask teachers/mentors who observed you over time.',
        'Provide a brag sheet (activities, goals, anecdotes) and the deadline.',
        'Ask 3-4 weeks in advance; send a friendly reminder a week before.',
        'Thank them and share outcomes afterward.'
      ],
      colorClass: 'green'
    },
    {
      title: 'Have Documents Ready',
      description: 'Outline common documents committees request.',
      points: [
        'Unofficial/official transcript (have PDFs ready to submit).',
        'SAT/ACT score report if required.',
        'Activity list or resume (1 page; impact-focused).',
        'Portfolio or links (for arts, coding, design, research).'
      ],
      colorClass: 'purple'
    },
    {
      title: 'Test Scores: Use Strategically',
      description: 'Clarify that scores are one data point; submit only if they strengthen the application when optional.',
      points: [
        'Check each program\'s policy (required vs. optional).',
        'If optional, send scores when they are at/above typical recipient ranges.',
        'Balance testing time with essay quality and leadership.'
      ],
      colorClass: 'pink'
    },
    {
      title: 'Deadlines, Fit, and Follow-Through',
      description: 'Encourage building a calendar, aligning fit with mission, and thorough final checks.',
      points: [
        'Build a deadlines calendar with internal milestones.',
        'Tailor each application: mirror the program\'s priorities.',
        'Proofread on a different day/device; check links and file names.',
        'Submit a day early to avoid technical issues.'
      ],
      colorClass: 'orange'
    },
    {
      title: 'Interview Preparation (If Applicable)',
      description: 'Provide basics for preparing and showcasing impact.',
      points: [
        'Prepare 3 key stories (challenge, leadership, impact).',
        'Practice aloud; time answers to 60-90 seconds.',
        'Research the organization and prepare 2 thoughtful questions.'
      ],
      colorClass: 'peach'
    }
  ];

  readonly checklist: string[] = [
    'Recommendation requests sent, with reminders scheduled.',
    'Resume/activity list updated and concise.',
    'Required scores or supplemental materials attached.',
    'All links tested; submit at least 24 hours early.'
  ];

  // TrackBy function - CRITICAL for performance
  trackByIndex(index: number): number {
    return index;
  }
}