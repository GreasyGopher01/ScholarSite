// auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

declare const google: any;

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  provider: 'google' | 'apple' | 'email';
  createdAt?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser: Observable<User | null>;
  private apiUrl = 'http://localhost:8000/api';
  public redirectUrl: string | null = null;

  constructor(private http: HttpClient, private router: Router) {
    const storedUser = localStorage.getItem('currentUser');
    this.currentUserSubject = new BehaviorSubject<User | null>(
      storedUser ? JSON.parse(storedUser) : null
    );
    this.currentUser = this.currentUserSubject.asObservable();
  }

  public get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  public get isAuthenticated(): boolean {
    return !!this.currentUserSubject.value;
  }

  // Initialize Google Sign-In and optionally render the button after initialization
  initGoogleAuth(element?: HTMLElement): void {
    if (typeof google !== 'undefined') {
      console.log('Google SDK loaded, initializing sign-in');
      google.accounts.id.initialize({
        client_id: '1068695482466-q6q5kllteel8ue5b4guv6qephtgdqhjm.apps.googleusercontent.com',
        callback: (response: any) => this.handleGoogleCallback(response),
        auto_select: false,
        cancel_on_tap_outside: true
      });

      if (element) {
        this.renderGoogleButton(element);
      }
    }
  }

  // Render Google Sign-In button
  renderGoogleButton(element: HTMLElement): void {
    if (typeof google !== 'undefined') {
      console.log('Rendering Google Sign-In button');
      google.accounts.id.renderButton(
        element,
        { 
          theme: 'outline', 
          size: 'large',
          width: 280,
          text: 'continue_with'
        }
      );
    }
  }

  setRedirectUrl(url: string | null): void {
    this.redirectUrl = url;
  }

  // Handle Google callback
  private handleGoogleCallback(response: any): void {
    console.log('Google callback received', response);
    const credential = response?.credential;
    if (!credential) {
      console.error('Google callback missing credential', response);
      return;
    }

    this.loginWithGoogle(credential).subscribe({
      next: (authResponse) => {
        console.log('Google login successful', authResponse);
        const destination = this.redirectUrl || '/home';
        this.redirectUrl = null;
        this.router.navigateByUrl(destination);
      },
      error: (error) => {
        console.error('Google login failed', error);
      }
    });
  }

  // Login with Google
  loginWithGoogle(credential: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/google`, { credential })
      .pipe(
        tap(response => this.setCurrentUser(response))
      );
  }

  // Login with Apple
  loginWithApple(authorizationCode: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/apple`, { 
      authorizationCode 
    }).pipe(
      tap(response => this.setCurrentUser(response))
    );
  }

  // Email/Password Login
  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/login`, { 
      email, 
      password 
    }).pipe(
      tap(response => this.setCurrentUser(response))
    );
  }

  // Email/Password Register
  register(name: string, email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/register`, { 
      name,
      email, 
      password 
    }).pipe(
      tap(response => this.setCurrentUser(response))
    );
  }

  // Update user profile
  updateProfile(updates: Partial<User>): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/auth/profile`, updates)
      .pipe(
        tap(user => {
          const currentUser = this.currentUserValue;
          if (currentUser) {
            const updatedUser = { ...currentUser, ...user };
            localStorage.setItem('currentUser', JSON.stringify(updatedUser));
            this.currentUserSubject.next(updatedUser);
          }
        })
      );
  }

  // Upload profile picture
  uploadProfilePicture(file: File): Observable<{ pictureUrl: string }> {
    const formData = new FormData();
    formData.append('picture', file);
    
    return this.http.post<{ pictureUrl: string }>(
      `${this.apiUrl}/auth/profile/picture`, 
      formData
    ).pipe(
      tap(response => {
        const currentUser = this.currentUserValue;
        if (currentUser) {
          currentUser.picture = response.pictureUrl;
          localStorage.setItem('currentUser', JSON.stringify(currentUser));
          this.currentUserSubject.next(currentUser);
        }
      })
    );
  }

  // Logout
  logout(): void {
    localStorage.removeItem('currentUser');
    localStorage.removeItem('authToken');
    this.currentUserSubject.next(null);
    
    // Sign out from Google
    if (typeof google !== 'undefined') {
      google.accounts.id.disableAutoSelect();
    }
  }

  // Set current user and token
  private setCurrentUser(response: AuthResponse): void {
    localStorage.setItem('currentUser', JSON.stringify(response.user));
    localStorage.setItem('authToken', response.token);
    this.currentUserSubject.next(response.user);
  }

  // Get auth token
  getToken(): string | null {
    return localStorage.getItem('authToken');
  }

  getUserBookmarks(): Observable<number[]> {
    return this.http.get<number[]>(`${this.apiUrl}/bookmarks`);
  }

  addBookmark(id: number): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/bookmarks`, { opportunityId: id });
  }

  removeBookmark(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/bookmarks/${id}`);
  }
}
