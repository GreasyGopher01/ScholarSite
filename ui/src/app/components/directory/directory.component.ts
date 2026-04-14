// directory.component.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';
import { environment } from '../../../environments/environment';

interface Opportunity {
  id: number;
  title: string;
  description: string;
  category: string;
  state: string;
  cost: string;
  deadline: string;
  location: string;
  sourceLink?: string;
}

@Component({
  selector: 'app-directory',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './directory.component.html',
  styleUrls: ['./directory.component.css']
})
export class DirectoryComponent implements OnInit {
  opportunities: Opportunity[] = [];
  filteredOpportunities: Opportunity[] = [];
  bookmarkedIds: number[] = [];

  // Filter values
  selectedCategory: string = 'All Categories';
  selectedState: string = 'All States';
  keywordFilter: string = '';
  deadlineFilter: string = '';

  categories: string[] = ['All Categories'];
  states: string[] = ['All States'];

  // Share modal
  showShareModal: boolean = false;
  selectedOpportunity: Opportunity | null = null;
  
  // Details modal
  showDetailsModal: boolean = false;

  // Pagination
  currentPage: number = 1;
  itemsPerPage: number = 10;
  totalPages: number = 1;
  itemsPerPageOptions: number[] = [5, 10, 15, 20, 25, 50];

  private apiUrl = environment.apiUrl;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    console.log('🚀 Directory component initialized - NEW VERSION');
    this.loadOpportunities();
    this.loadBookmarks();
  }

  loadOpportunities(): void {
    console.log('🔵 Starting to load opportunities...');
    this.http.get<Opportunity[]>(`${this.apiUrl}/opportunities`).subscribe({
      next: (data) => {
        console.log('✅ SUCCESS! Received opportunities:', data);
        console.log('📊 Total count:', data.length);
        
        this.opportunities = data;
        this.filteredOpportunities = data;
        
        console.log('🎯 Set opportunities array:', this.opportunities.length);
        console.log('🎯 Set filteredOpportunities array:', this.filteredOpportunities.length);
        
        this.extractFilters();
        this.updatePagination();
        
        console.log('🔄 Calling change detection...');
        this.cdr.markForCheck();
        this.cdr.detectChanges();
        console.log('✨ Change detection complete!');
      },
      error: (error) => {
        console.error('❌ ERROR loading opportunities:', error);
      }
    });
  }

  loadBookmarks(): void {
    if (!this.authService.isAuthenticated) {
      this.bookmarkedIds = [];
      return;
    }
    
    this.authService.getUserBookmarks().subscribe({
      next: (bookmarks) => {
        this.bookmarkedIds = bookmarks;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error loading bookmarks:', error);
        this.bookmarkedIds = [];
      }
    });
  }

  extractFilters(): void {
    const categorySet = new Set<string>();
    const stateSet = new Set<string>();

    this.opportunities.forEach(opp => {
      if (opp.category) categorySet.add(opp.category);
      if (opp.state) stateSet.add(opp.state);
    });

    this.categories = ['All Categories', ...Array.from(categorySet).sort()];
    this.states = ['All States', ...Array.from(stateSet).sort()];
    
    console.log('📋 Extracted categories:', this.categories);
    console.log('📋 Extracted states:', this.states);
  }

  applyFilters(): void {
    console.log('🔍 Applying filters...');
    
    this.filteredOpportunities = this.opportunities.filter(opp => {
      const matchesCategory = this.selectedCategory === 'All Categories' || 
                              opp.category === this.selectedCategory;
      
      const matchesState = this.selectedState === 'All States' || 
                          opp.state === this.selectedState;
      
      const matchesKeyword = !this.keywordFilter || 
                            opp.title.toLowerCase().includes(this.keywordFilter.toLowerCase()) ||
                            opp.description.toLowerCase().includes(this.keywordFilter.toLowerCase());
      
      const matchesDeadline = !this.deadlineFilter || 
                             new Date(opp.deadline) >= new Date(this.deadlineFilter);

      return matchesCategory && matchesState && matchesKeyword && matchesDeadline;
    });
    
    console.log('🎯 Filtered results:', this.filteredOpportunities.length);
    
    // Reset to first page when filters change
    this.currentPage = 1;
    this.updatePagination();
    
    this.cdr.detectChanges();
  }

  updatePagination(): void {
    this.totalPages = Math.ceil(this.filteredOpportunities.length / this.itemsPerPage);
    if (this.currentPage > this.totalPages && this.totalPages > 0) {
      this.currentPage = this.totalPages;
    }
    console.log('📄 Pagination updated - Total pages:', this.totalPages, 'Current page:', this.currentPage);
  }

  onItemsPerPageChange(): void {
    // Ensure itemsPerPage is a number, not a string
    this.itemsPerPage = Number(this.itemsPerPage);
    console.log('📊 Items per page changed to:', this.itemsPerPage, 'Type:', typeof this.itemsPerPage);
    this.currentPage = 1; // Reset to first page
    this.updatePagination();
    this.cdr.detectChanges();
  }

  getPaginatedOpportunities(): Opportunity[] {
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    const paginated = this.filteredOpportunities.slice(startIndex, endIndex);
    console.log(`📑 Page ${this.currentPage}: Showing items ${startIndex + 1}-${Math.min(endIndex, this.filteredOpportunities.length)} of ${this.filteredOpportunities.length}`);
    console.log(`📦 Returning ${paginated.length} items`);
    return paginated;
  }

  getStartIndex(): number {
    return (this.currentPage - 1) * this.itemsPerPage + 1;
  }

  getEndIndex(): number {
    const endIndex = this.currentPage * this.itemsPerPage;
    return Math.min(endIndex, this.filteredOpportunities.length);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      window.scrollTo({ top: 0, behavior: 'smooth' });
      this.cdr.detectChanges();
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.goToPage(this.currentPage + 1);
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.goToPage(this.currentPage - 1);
    }
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxPagesToShow = 5;
    
    if (this.totalPages <= maxPagesToShow) {
      for (let i = 1; i <= this.totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (this.currentPage <= 3) {
        for (let i = 1; i <= 4; i++) {
          pages.push(i);
        }
        pages.push(-1); // Ellipsis
        pages.push(this.totalPages);
      } else if (this.currentPage >= this.totalPages - 2) {
        pages.push(1);
        pages.push(-1);
        for (let i = this.totalPages - 3; i <= this.totalPages; i++) {
          pages.push(i);
        }
      } else {
        pages.push(1);
        pages.push(-1);
        for (let i = this.currentPage - 1; i <= this.currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push(-1);
        pages.push(this.totalPages);
      }
    }
    
    return pages;
  }

  isBookmarked(id: number): boolean {
    return this.bookmarkedIds.includes(id);
  }

  toggleBookmark(id: number): void {
    if (!this.authService.isAuthenticated) {
      alert('Please sign in to bookmark opportunities');
      return;
    }
    
    if (this.isBookmarked(id)) {
      this.authService.removeBookmark(id).subscribe({
        next: () => {
          this.bookmarkedIds = this.bookmarkedIds.filter(bId => bId !== id);
          this.cdr.detectChanges();
        },
        error: (error) => {
          console.error('Error removing bookmark:', error);
        }
      });
    } else {
      this.authService.addBookmark(id).subscribe({
        next: () => {
          this.bookmarkedIds.push(id);
          this.cdr.detectChanges();
        },
        error: (error) => {
          console.error('Error adding bookmark:', error);
        }
      });
    }
  }

  getCategoryColor(category: string): string {
    const colors: {[key: string]: string} = {
      'Courses': '#5DADE2',
      'Grants': '#52C7B8',
      'Training Programs': '#5499C7',
      'Scholarship': '#9B59B6',
      'Fellowship': '#E74C3C',
      'Apprenticeship': '#F39C12',
      'Bootcamp': '#3498DB',
      'Internship': '#16A085'
    };
    return colors[category] || '#5DADE2';
  }

  formatDeadline(deadline: string): string {
    const date = new Date(deadline);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  }

  openDetailsModal(opp: Opportunity): void {
    this.selectedOpportunity = opp;
    this.showDetailsModal = true;
  }

  closeDetailsModal(): void {
    this.showDetailsModal = false;
    this.selectedOpportunity = null;
  }

  openShareModal(opp: Opportunity): void {
    this.selectedOpportunity = opp;
    this.showShareModal = true;
  }

  closeShareModal(): void {
    this.showShareModal = false;
  }

  shareViaEmail(): void {
    if (!this.selectedOpportunity) return;
    const subject = encodeURIComponent(`Check out this opportunity: ${this.selectedOpportunity.title}`);
    const body = encodeURIComponent(`${this.selectedOpportunity.description}\n\nLearn more at: ${window.location.href}`);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  }

  shareOnFacebook(): void {
    if (!this.selectedOpportunity) return;
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank', 'width=600,height=400');
  }

  shareOnTwitter(): void {
    if (!this.selectedOpportunity) return;
    const text = encodeURIComponent(`Check out this opportunity: ${this.selectedOpportunity.title}`);
    const url = encodeURIComponent(window.location.href);
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank', 'width=600,height=400');
  }

  shareOnLinkedIn(): void {
    if (!this.selectedOpportunity) return;
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank', 'width=600,height=400');
  }

  trackByOpportunityId(index: number, opportunity: Opportunity): number {
    return opportunity.id;
  }
}