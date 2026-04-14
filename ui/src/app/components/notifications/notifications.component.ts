// notifications.component.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { RouterLink } from '@angular/router';
import { environment } from '../../../environments/environment';

interface Subscription {
  id?: number;
  email: string;
  states: string[];
  categories: string[];
  created_at: string;
}

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.css']
})
export class NotificationsComponent implements OnInit {
  email: string = '';
  selectedStates: string[] = [];
  selectedCategories: string[] = [];
  
  availableStates: string[] = [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 
    'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
    'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa',
    'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
    'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri',
    'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey',
    'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
    'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
    'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
    'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming',
    'National'
  ];
  availableCategories: string[] = [];
  
  activeSubscriptions: Subscription[] = [];
  submitting: boolean = false;
  successMessage: string = '';
  errorMessage: string = '';

  private apiUrl = environment.apiUrl;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    console.log('🚀 Notifications component initialized');
    this.loadCategories();
    this.loadSubscriptions();
  }

  loadCategories(): void {
    this.http.get<any[]>(`${this.apiUrl}/opportunities`).subscribe({
      next: (opportunities) => {
        const categorySet = new Set<string>();

        opportunities.forEach(opp => {
          if (opp.category) categorySet.add(opp.category);
        });

        this.availableCategories = Array.from(categorySet).sort();
        
        console.log('✅ Loaded categories:', this.availableCategories.length);
        
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('❌ Error loading categories:', error);
      }
    });
  }

  loadSubscriptions(): void {
    this.http.get<Subscription[]>(`${this.apiUrl}/subscriptions`).subscribe({
      next: (data) => {
        this.activeSubscriptions = data.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        console.log('✅ Loaded subscriptions:', this.activeSubscriptions.length);
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('❌ Error loading subscriptions:', error);
      }
    });
  }

  subscribe(): void {
    // Validation
    if (!this.email.trim()) {
      this.showError('Please enter your email address');
      return;
    }

    if (!this.isValidEmail(this.email)) {
      this.showError('Please enter a valid email address');
      return;
    }

    if (this.selectedStates.length === 0) {
      this.showError('Please select at least one state');
      return;
    }

    if (this.selectedCategories.length === 0) {
      this.showError('Please select at least one category');
      return;
    }

    this.submitting = true;
    this.errorMessage = '';

    const subscription: Subscription = {
      email: this.email.trim().toLowerCase(),
      states: this.selectedStates,
      categories: this.selectedCategories,
      created_at: new Date().toISOString()
    };

    this.http.post(`${this.apiUrl}/subscriptions`, subscription).subscribe({
      next: (response) => {
        console.log('✅ Subscription created:', response);
        
        this.successMessage = 'Successfully subscribed! You will receive notifications about new opportunities matching your preferences.';
        setTimeout(() => {
          this.successMessage = '';
          this.cdr.detectChanges();
        }, 5000);

        // Clear form
        this.email = '';
        this.selectedStates = [];
        this.selectedCategories = [];

        // Reload subscriptions
        this.loadSubscriptions();
        
        this.submitting = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('❌ Error creating subscription:', error);
        this.showError('Error creating subscription. Please try again.');
        this.submitting = false;
        this.cdr.detectChanges();
      }
    });
  }

  unsubscribe(id: number): void {
    if (!confirm('Are you sure you want to unsubscribe?')) {
      return;
    }

    this.http.delete(`${this.apiUrl}/subscriptions/${id}`).subscribe({
      next: () => {
        console.log('✅ Unsubscribed successfully');
        this.loadSubscriptions();
      },
      error: (error) => {
        console.error('❌ Error unsubscribing:', error);
        alert('Error unsubscribing. Please try again.');
      }
    });
  }

  isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  showError(message: string): void {
    this.errorMessage = message;
    setTimeout(() => {
      this.errorMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }
}