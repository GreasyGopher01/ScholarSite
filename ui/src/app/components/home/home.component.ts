// home.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent {
  features = [
    {
      text: 'Explore our Directory for all of our available opportunities!',
      color: '#7DCEA0'
    },
    {
      text: 'Save your favorite opportunities under Bookmarks!',
      color: '#76D7C4'
    },
    {
      text: 'Check out our Tips to Success for crucial application advice!',
      color: '#5DADE2'
    },
    {
      text: 'Discover more events you\'ll love under Recommendations!',
      color: '#5DADE2'
    },
    {
      text: 'Share your advice and thoughts with us in Feedback!',
      color: '#5499C7'
    },
    {
      text: 'Sign up in Notifications to be the first to hear of new events!',
      color: '#85C1E9'
    }
  ];

  quickLinks = [
    { name: 'Home', route: '/' },
    { name: 'Directory', route: '/directory' },
    { name: 'Bookmarks', route: '/bookmarks' },
    { name: 'Recommendations', route: '/recommendations' },
    { name: 'Tips to Success', route: '/tips' }
  ];
}