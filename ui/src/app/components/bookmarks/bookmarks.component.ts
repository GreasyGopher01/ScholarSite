// bookmarks.component.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { RouterLink } from '@angular/router';

interface Opportunity {
  id: number;
  title: string;
  description: string;
  category: string;
  state: string;
  cost: string;
  deadline: string;
  location: string;
  tags?: string[];
}

@Component({
  selector: 'app-bookmarks',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './bookmarks.component.html',
  styleUrls: ['./bookmarks.component.css']
})
export class BookmarksComponent implements OnInit {
  bookmarkedOpportunities: Opportunity[] = [];
  selectedOpportunity: Opportunity | null = null;
  showTagModal: boolean = false;
  showDetailsModal: boolean = false;
  showShareModal: boolean = false;
  newTag: string = '';

  // Pagination
  currentPage: number = 1;
  itemsPerPage: number = 10;
  totalPages: number = 1;
  itemsPerPageOptions: number[] = [5, 10, 15, 20, 25, 50];

    //private apiUrl = 'http://localhost:8000';
  private apiUrl = 'https://scholarsite-1.onrender.com';

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    console.log('🚀 Bookmarks component initialized - NEW VERSION');
    this.loadBookmarks();
  }

  loadBookmarks(): void {
    console.log('🔵 Loading bookmarks...');
    this.http.get<{id: number}[]>(`${this.apiUrl}/bookmarks`).subscribe({
      next: (bookmarks) => {
        console.log('✅ Received bookmarks:', bookmarks);
        const bookmarkIds = bookmarks.map(b => b.id);
        console.log('📌 Bookmark IDs:', bookmarkIds);
        
        this.http.get<Opportunity[]>(`${this.apiUrl}/opportunities`).subscribe({
          next: (opportunities) => {
            console.log('✅ Received all opportunities:', opportunities);
            this.bookmarkedOpportunities = opportunities.filter(opp => 
              bookmarkIds.includes(opp.id)
            ).map(opp => ({
              ...opp,
              tags: []
            }));
            console.log('🎯 Filtered bookmarked opportunities:', this.bookmarkedOpportunities);
            console.log('📊 Count:', this.bookmarkedOpportunities.length);
            
            this.updatePagination();
            
            console.log('🔄 Triggering change detection...');
            this.cdr.markForCheck();
            this.cdr.detectChanges();
            console.log('✨ Change detection complete!');
          },
          error: (error) => {
            console.error('❌ Error loading opportunities:', error);
          }
        });
      },
      error: (error) => {
        console.error('❌ Error loading bookmarks:', error);
      }
    });
  }

  removeBookmark(id: number): void {
    this.http.delete(`${this.apiUrl}/bookmarks/${id}`).subscribe({
      next: () => {
        this.bookmarkedOpportunities = this.bookmarkedOpportunities.filter(
          opp => opp.id !== id
        );
        this.updatePagination();
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error removing bookmark:', error);
      }
    });
  }

  openTagModal(opp: Opportunity): void {
    this.selectedOpportunity = opp;
    this.showTagModal = true;
  }

  closeTagModal(): void {
    this.showTagModal = false;
    this.selectedOpportunity = null;
    this.newTag = '';
  }

  addTag(): void {
    if (!this.selectedOpportunity || !this.newTag.trim()) return;
    
    if (!this.selectedOpportunity.tags) {
      this.selectedOpportunity.tags = [];
    }
    
    if (!this.selectedOpportunity.tags.includes(this.newTag.trim())) {
      this.selectedOpportunity.tags.push(this.newTag.trim());
    }
    
    this.newTag = '';
    this.closeTagModal();
  }

  removeTag(opp: Opportunity, tag: string): void {
    if (opp.tags) {
      opp.tags = opp.tags.filter(t => t !== tag);
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
    const subject = encodeURIComponent(`Check out: ${this.selectedOpportunity.title}`);
    const body = encodeURIComponent(this.selectedOpportunity.description);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  }

  shareOnFacebook(): void {
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank', 'width=600,height=400');
  }

  shareOnTwitter(): void {
    if (!this.selectedOpportunity) return;
    const text = encodeURIComponent(`Check out: ${this.selectedOpportunity.title}`);
    window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank', 'width=600,height=400');
  }

  shareOnLinkedIn(): void {
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank', 'width=600,height=400');
  }

  // Pagination methods
  updatePagination(): void {
    this.totalPages = Math.ceil(this.bookmarkedOpportunities.length / this.itemsPerPage);
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
    const paginated = this.bookmarkedOpportunities.slice(startIndex, endIndex);
    console.log(`📑 Page ${this.currentPage}: Showing items ${startIndex + 1}-${Math.min(endIndex, this.bookmarkedOpportunities.length)} of ${this.bookmarkedOpportunities.length}`);
    console.log(`📦 Returning ${paginated.length} items`);
    return paginated;
  }

  getStartIndex(): number {
    return Math.min((this.currentPage - 1) * this.itemsPerPage + 1, this.bookmarkedOpportunities.length);
  }

  getEndIndex(): number {
    const endIndex = this.currentPage * this.itemsPerPage;
    return Math.min(endIndex, this.bookmarkedOpportunities.length);
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
        pages.push(-1);
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
}
