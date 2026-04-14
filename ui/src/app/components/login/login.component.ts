// login.component.ts
import { Component, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService, User } from '../../services/auth.service';
import { Subscription } from 'rxjs';

declare var google: any;

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit, AfterViewInit, OnDestroy {
  isLoading = false;
  errorMessage = '';
  private authSubscription?: Subscription;
  private returnUrl = '/home';

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') || '/home';
    this.authService.setRedirectUrl(this.returnUrl);

    if (this.authService.isAuthenticated) {
      this.router.navigateByUrl(this.returnUrl);
    }

    this.authSubscription = this.authService.currentUser.subscribe((user: User | null) => {
      if (user) {
        this.router.navigateByUrl(this.returnUrl);
      }
    });
  }

  ngAfterViewInit(): void {
    const googleButtonElement = document.getElementById('googleSignInButton');
    if (googleButtonElement) {
      this.waitForGoogle(() => this.authService.initGoogleAuth(googleButtonElement));
    }
  }

  ngOnDestroy(): void {
    this.authSubscription?.unsubscribe();
  }

  private waitForGoogle(callback: () => void, retries = 12): void {
    if (typeof google !== 'undefined') {
      callback();
    } else if (retries > 0) {
      setTimeout(() => this.waitForGoogle(callback, retries - 1), 250);
    } else {
      console.warn('Google Sign-In SDK did not load in time.');
    }
  }
}
