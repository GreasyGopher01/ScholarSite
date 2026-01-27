import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getOpportunities(): Observable<any[]> {
    return this.http.get<any[]>(this.baseUrl + '/opportunities');
  }

  getTips(): Observable<any[]> {
    return this.http.get<any[]>(this.baseUrl + '/tips');
  }

  getBookmarks(): Observable<any[]> {
    return this.http.get<any[]>(this.baseUrl + '/bookmarks');
  }

  addBookmark(id: number): Observable<any> {
    return this.http.post(this.baseUrl + '/bookmarks/' + id, {});
  }

  sendFeedback(message: string): Observable<any> {
    return this.http.post(this.baseUrl + '/feedback', { message: message });
  }

  subscribe(email: string): Observable<any> {
    return this.http.post(this.baseUrl + '/notifications', { email: email });
  }

  getRecommendations(): Observable<any> {
    return this.http.get<any>(this.baseUrl + '/recommendations');
  }
}
