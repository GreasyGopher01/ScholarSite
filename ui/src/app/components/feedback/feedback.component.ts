// feedback.component.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { RouterLink } from '@angular/router';

interface Feedback {
  id?: number;
  title: string;
  body: string;
  timestamp: string;
}

@Component({
  selector: 'app-feedback',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './feedback.component.html',
  styleUrls: ['./feedback.component.css']
})
export class FeedbackComponent implements OnInit {
  title: string = '';
  body: string = '';
  feedbackList: Feedback[] = [];
  submitting: boolean = false;
  successMessage: string = '';

    //private apiUrl = 'http://localhost:8000';
  private apiUrl = 'https://scholarsite-1.onrender.com';

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    console.log('🚀 Feedback component initialized');
    this.loadFeedback();
  }

  loadFeedback(): void {
    this.http.get<Feedback[]>(`${this.apiUrl}/feedback`).subscribe({
      next: (data) => {
        this.feedbackList = data.sort((a, b) => 
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
        console.log('✅ Loaded feedback:', this.feedbackList.length);
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('❌ Error loading feedback:', error);
      }
    });
  }

  submitFeedback(): void {
    if (!this.title.trim() || !this.body.trim()) {
      alert('Please fill in both title and body fields');
      return;
    }

    this.submitting = true;

    const feedback: Feedback = {
      title: this.title.trim(),
      body: this.body.trim(),
      timestamp: new Date().toISOString()
    };

    this.http.post(`${this.apiUrl}/feedback`, feedback).subscribe({
      next: (response) => {
        console.log('✅ Feedback submitted:', response);
        
        // Show success message
        this.successMessage = 'Thank you for your feedback!';
        setTimeout(() => {
          this.successMessage = '';
          this.cdr.detectChanges();
        }, 3000);

        // Clear form
        this.title = '';
        this.body = '';

        // Reload feedback list
        this.loadFeedback();
        
        this.submitting = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('❌ Error submitting feedback:', error);
        alert('Error submitting feedback. Please try again.');
        this.submitting = false;
        this.cdr.detectChanges();
      }
    });
  }

  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  }

  getTimeAgo(timestamp: string): string {
    const now = new Date().getTime();
    const then = new Date(timestamp).getTime();
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return this.formatTimestamp(timestamp);
  }
}
