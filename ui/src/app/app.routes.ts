// app.routes.ts
import { Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { DirectoryComponent } from './components/directory/directory.component';
import { BookmarksComponent } from './components/bookmarks/bookmarks.component';
import { RecommendationsComponent } from './components/recommendations/recommendations.component';
import { FeedbackComponent } from './components/feedback/feedback.component';
import { TipsComponent } from './components/tips/tips.component';
import { NotificationsComponent } from './components/notifications/notifications.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'directory', component: DirectoryComponent },
  { path: 'bookmarks', component: BookmarksComponent },
  { path: 'recommendations', component: RecommendationsComponent },
  { path: 'feedback', component: FeedbackComponent },
  { path: 'tips', component: TipsComponent },
  { path: 'notifications', component: NotificationsComponent },
  { path: '**', redirectTo: '' }
];