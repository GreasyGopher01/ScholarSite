// recommendations.component.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
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
  tags?: string;
  sourceLink?: string;
}

interface RecommendationScore {
  opportunity: Opportunity;
  score: number;
  reasons: string[];
}

@Component({
  selector: 'app-recommendations',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './recommendations.component.html',
  styleUrls: ['./recommendations.component.css']
})
export class RecommendationsComponent implements OnInit {
  recommendations: Opportunity[] = [];
  bookmarkedOpportunities: Opportunity[] = [];
  allOpportunities: Opportunity[] = [];
  bookmarkedIds: number[] = [];
  loading: boolean = true;

  // Modal states
  showDetailsModal: boolean = false;
  showShareModal: boolean = false;
  selectedOpportunity: Opportunity | null = null;

  // Pagination
  currentPage: number = 1;
  itemsPerPage: number = 10;
  totalPages: number = 1;

  private apiUrl = environment.apiUrl;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    console.log('🚀 Recommendations component initialized');
    if (!this.authService.isAuthenticated) {
      console.warn('Recommendations require login; redirecting to /login');
      this.router.navigate(['/login']);
      return;
    }
    this.loadRecommendations();
  }

  loadRecommendations(): void {
    this.loading = true;
    
    // Load bookmarks using authenticated API
    this.authService.getUserBookmarks().subscribe({
      next: (bookmarkIds) => {
        this.bookmarkedIds = bookmarkIds;
        
        // Load all opportunities
        this.http.get<Opportunity[]>(`${this.apiUrl}/opportunities`).subscribe({
          next: (opportunities) => {
            this.allOpportunities = opportunities;
            this.bookmarkedOpportunities = opportunities.filter(opp => 
              this.bookmarkedIds.includes(opp.id)
            );
            
            console.log('📚 Bookmarked opportunities:', this.bookmarkedOpportunities.length);
            
            // Generate recommendations
            this.recommendations = this.generateRecommendations();
            
            console.log('✨ Generated recommendations:', this.recommendations.length);
            this.updatePagination();
            this.loading = false;
            this.cdr.detectChanges();
          },
          error: (error) => {
            console.error('❌ Error loading opportunities:', error);
            this.loading = false;
          }
        });
      },
      error: (error) => {
        console.error('❌ Error loading bookmarks:', error);
        this.loading = false;
      }
    });
  }

  generateRecommendations(): Opportunity[] {
    if (this.bookmarkedOpportunities.length === 0) {
      // No bookmarks - return top 5 opportunities
      return this.allOpportunities.slice(0, 5);
    }

    // Analyze bookmarked opportunities
    const userProfile = this.analyzeUserProfile();
    
    console.log('👤 User profile:', userProfile);

    // Score all non-bookmarked opportunities
    const scoredOpportunities: RecommendationScore[] = this.allOpportunities
      .filter(opp => !this.bookmarkedIds.includes(opp.id))
      .map(opp => ({
        opportunity: opp,
        score: this.calculateRecommendationScore(opp, userProfile),
        reasons: this.getRecommendationReasons(opp, userProfile)
      }));

    // Sort by score and return top 10
    const topRecommendations = scoredOpportunities
      .sort((a, b) => b.score - a.score)
      .slice(0, 10)
      .map(scored => {
        console.log(`🎯 ${scored.opportunity.title}: Score ${scored.score} - ${scored.reasons.join(', ')}`);
        return scored.opportunity;
      });

    return topRecommendations;
  }

  analyzeUserProfile(): any {
    const categories = new Map<string, number>();
    const states = new Map<string, number>();
    const keywords = new Map<string, number>();
    const tags = new Map<string, number>();

    this.bookmarkedOpportunities.forEach(opp => {
      // Count categories
      categories.set(opp.category, (categories.get(opp.category) || 0) + 1);
      
      // Count states
      states.set(opp.state, (states.get(opp.state) || 0) + 1);
      
      // Extract keywords from title and description
      const text = `${opp.title} ${opp.description}`.toLowerCase();
      const words = text.match(/\b[a-z]{4,}\b/g) || [];
      
      words.forEach(word => {
        // Skip common words
        if (!this.isCommonWord(word)) {
          keywords.set(word, (keywords.get(word) || 0) + 1);
        }
      });

      // Extract tags if available
      if (opp.tags) {
        const oppTags = opp.tags.split(';');
        oppTags.forEach(tag => {
          tags.set(tag.trim(), (tags.get(tag.trim()) || 0) + 1);
        });
      }
    });

    return {
      categories: this.mapToArray(categories),
      states: this.mapToArray(states),
      keywords: this.mapToArray(keywords).slice(0, 20), // Top 20 keywords
      tags: this.mapToArray(tags)
    };
  }

  calculateRecommendationScore(opp: Opportunity, profile: any): number {
    let score = 0;

    // Category match (highest weight - 40 points)
    const categoryWeight = profile.categories.find((c: any) => c.key === opp.category);
    if (categoryWeight) {
      score += 40 * (categoryWeight.value / this.bookmarkedOpportunities.length);
    }

    // State match (20 points)
    const stateWeight = profile.states.find((s: any) => s.key === opp.state);
    if (stateWeight) {
      score += 20 * (stateWeight.value / this.bookmarkedOpportunities.length);
    }

    // Keyword match (30 points total)
    const text = `${opp.title} ${opp.description}`.toLowerCase();
    let keywordMatches = 0;
    profile.keywords.forEach((kw: any) => {
      if (text.includes(kw.key)) {
        keywordMatches += kw.value;
      }
    });
    score += Math.min(30, keywordMatches * 2);

    // Tag match (10 points)
    if (opp.tags) {
      const oppTags = opp.tags.split(';').map(t => t.trim());
      let tagMatches = 0;
      profile.tags.forEach((tag: any) => {
        if (oppTags.includes(tag.key)) {
          tagMatches += tag.value;
        }
      });
      score += Math.min(10, tagMatches * 2);
    }

    return score;
  }

  getRecommendationReasons(opp: Opportunity, profile: any): string[] {
    const reasons: string[] = [];

    // Check category match
    if (profile.categories.some((c: any) => c.key === opp.category)) {
      reasons.push(`Similar category: ${opp.category}`);
    }

    // Check state match
    if (profile.states.some((s: any) => s.key === opp.state)) {
      reasons.push(`Your preferred location: ${opp.state}`);
    }

    // Check keyword matches
    const text = `${opp.title} ${opp.description}`.toLowerCase();
    const matchedKeywords = profile.keywords
      .filter((kw: any) => text.includes(kw.key))
      .slice(0, 2)
      .map((kw: any) => kw.key);
    
    if (matchedKeywords.length > 0) {
      reasons.push(`Matches your interests: ${matchedKeywords.join(', ')}`);
    }

    return reasons.length > 0 ? reasons : ['Popular opportunity'];
  }

  mapToArray(map: Map<string, number>): any[] {
    return Array.from(map.entries())
      .map(([key, value]) => ({ key, value }))
      .sort((a, b) => b.value - a.value);
  }

  isCommonWord(word: string): boolean {
    const commonWords = [
      'this', 'that', 'with', 'from', 'have', 'more', 'will', 'their',
      'about', 'which', 'when', 'there', 'their', 'would', 'could',
      'other', 'these', 'some', 'into', 'your', 'what', 'than'
    ];
    return commonWords.includes(word);
  }

  isBookmarked(id: number): boolean {
    return this.bookmarkedIds.includes(id);
  }

  toggleBookmark(id: number): void {
    if (this.isBookmarked(id)) {
      this.authService.removeBookmark(id).subscribe({
        next: () => {
          this.bookmarkedIds = this.bookmarkedIds.filter(bId => bId !== id);
          this.loadRecommendations();
        },
        error: (error) => {
          console.error('❌ Error removing bookmark:', error);
        }
      });
    } else {
      this.authService.addBookmark(id).subscribe({
        next: () => {
          this.bookmarkedIds.push(id);
          this.loadRecommendations();
        },
        error: (error) => {
          console.error('❌ Error adding bookmark:', error);
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
    this.totalPages = Math.ceil(this.recommendations.length / this.itemsPerPage);
    if (this.currentPage > this.totalPages && this.totalPages > 0) {
      this.currentPage = this.totalPages;
    }
  }

  getPaginatedRecommendations(): Opportunity[] {
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    return this.recommendations.slice(startIndex, endIndex);
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