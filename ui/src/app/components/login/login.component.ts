// login.component.ts
import { Component, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService, AuthResponse, User } from '../../services/auth.service';
import { Subscription } from 'rxjs';

declare var google: any;
declare var AppleID: any;

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit, AfterViewInit, OnDestroy {
  loginForm: FormGroup;
  isLoading = false;
  errorMessage = '';
  private authSubscription?: Subscription;
  private returnUrl = '/home';

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.loginForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      rememberMe: [false]
    });
  }

  ngOnInit(): void {
    this.returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') || '/home';
    this.authService.setRedirectUrl(this.returnUrl);

    // Redirect if already logged in
    if (this.authService.isAuthenticated) {
      this.router.navigateByUrl(this.returnUrl);
    }

    this.authSubscription = this.authService.currentUser.subscribe((user: User | null) => {
      if (user) {
        this.router.navigateByUrl(this.returnUrl);
      }
    });

    // Initialize Apple Sign In once the SDK is available
    this.waitForApple(() => this.initAppleSignIn());
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

  private waitForApple(callback: () => void, retries = 12): void {
    if (typeof AppleID !== 'undefined') {
      callback();
    } else if (retries > 0) {
      setTimeout(() => this.waitForApple(callback, retries - 1), 250);
    } else {
      console.warn('Apple Sign-In SDK did not load in time.');
    }
  }

  initAppleSignIn(): void {
    if (typeof AppleID !== 'undefined') {
      AppleID.auth.init({
        clientId: 'YOUR_APPLE_CLIENT_ID',
        scope: 'name email',
        redirectURI: 'https://your-domain.com/auth/apple/callback',
        state: 'origin:web',
        usePopup: true
      });

      // Listen for authorization success
      document.addEventListener('AppleIDSignInOnSuccess', (event: any) => {
        console.log('Apple Sign In Success:', event.detail);
        this.handleAppleSignIn(event.detail.authorization);
      });

      // Listen for authorization failure
      document.addEventListener('AppleIDSignInOnFailure', (event: any) => {
        console.error('Apple Sign In Error:', event.detail.error);
        this.errorMessage = 'Apple Sign In failed. Please try again.';
      });
    }
  }

  handleAppleSignIn(authorization: any): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.authService.loginWithApple(authorization.code).subscribe({
      next: (response: AuthResponse) => {
        console.log('Apple login successful', response);
        this.router.navigateByUrl(this.returnUrl);
      },
      error: (error: any) => {
        console.error('Apple login failed', error);
        this.errorMessage = error.error?.message || 'Apple Sign In failed';
        this.isLoading = false;
      }
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    const { email, password } = this.loginForm.value;

    this.authService.login(email, password).subscribe({
      next: (response: AuthResponse) => {
        console.log('Login successful', response);
        this.router.navigateByUrl(this.returnUrl);
      },
      error: (error: any) => {
        console.error('Login failed', error);
        this.errorMessage = error.error?.message || 'Invalid email or password';
        this.isLoading = false;
      }
    });
  }
}
