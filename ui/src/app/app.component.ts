// app.component.ts
import { Component } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink],
  template: `
    <div class="app-shell">
      <header class="app-header">
        <div class="brand">
          <a routerLink="/home">ScholarSite</a>
        </div>
        <div class="user-panel" *ngIf="authService.currentUser | async as user; else guest">
          <span class="user-name">Hello, {{ user.name }}</span>
          <a routerLink="/profile" class="profile-link">Profile</a>
        </div>
        <ng-template #guest>
          <a routerLink="/login" class="login-link">Sign In</a>
        </ng-template>
      </header>
      <main class="app-main">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styles: [
    `:host { display: block; min-height: 100vh; background: #f7fafc; }
     .app-shell { display: flex; flex-direction: column; min-height: 100vh; }
     .app-header { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1.5rem; background: #ffffff; border-bottom: 1px solid #e2e8f0; }
     .brand a { text-decoration: none; font-weight: 700; color: #2d3748; font-size: 1.1rem; }
     .user-panel, .login-link { display: flex; align-items: center; gap: 0.75rem; color: #2d3748; }
     .user-name { font-weight: 600; }
     .profile-link, .login-link { text-decoration: none; color: #5a67d8; font-weight: 600; }
     .app-main { flex: 1; }
    `
  ]
})
export class AppComponent {
  constructor(public authService: AuthService) {}
}
