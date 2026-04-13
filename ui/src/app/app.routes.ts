// app.routes.ts
import { Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { LoginComponent } from './components/login/login.component';
import { ProfileComponent } from './components/profile/profile.component';

import { DirectoryComponent } from './components/directory/directory.component';
import { BookmarksComponent } from './components/bookmarks/bookmarks.component';
import { RecommendationsComponent } from './components/recommendations/recommendations.component';
import { FeedbackComponent } from './components/feedback/feedback.component';
import { TipsComponent } from './components/tips/tips.component';
import { NotificationsComponent } from './components/notifications/notifications.component';
import { authGuard } from './auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/home', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'home', component: HomeComponent },
  { path: 'profile', component: ProfileComponent, canActivate: [authGuard] },
  { path: 'directory', component: DirectoryComponent },
  { path: 'bookmarks', component: BookmarksComponent, canActivate: [authGuard] },
  { path: 'recommendations', component: RecommendationsComponent, canActivate: [authGuard] },
  { path: 'feedback', component: FeedbackComponent },
  { path: 'tips', component: TipsComponent },
  { path: 'notifications', component: NotificationsComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: '/home' }
];