// profile.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService, User } from '../../services/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.css']
})
export class ProfileComponent implements OnInit {
  user: User | null = null;
  profileForm: FormGroup;
  passwordForm: FormGroup;
  isSaving = false;
  isChangingPassword = false;
  successMessage = '';
  bookmarksCount = 0;
  applicationsCount = 0;
  savedCount = 0;

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.profileForm = this.formBuilder.group({
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone: [''],
      location: [''],
      bio: ['']
    });

    this.passwordForm = this.formBuilder.group({
      currentPassword: ['', Validators.required],
      newPassword: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', Validators.required]
    }, { 
      validators: this.passwordMatchValidator 
    });
  }

  ngOnInit(): void {
    this.authService.currentUser.subscribe((user: User | null) => {
      this.user = user;
      if (user) {
        this.profileForm.patchValue({
          name: user.name,
          email: user.email,
          phone: user.phone || '',
          location: user.location || '',
          bio: user.bio || ''
        });
        this.loadUserStats();
      } else {
        this.router.navigate(['/login']);
      }
    });
  }

  loadUserStats(): void {
    this.authService.getUserBookmarks().subscribe({
      next: (bookmarkIds: number[]) => {
        this.bookmarksCount = bookmarkIds.length;
        this.savedCount = bookmarkIds.length;
      },
      error: (error: any) => {
        console.error('Failed to load bookmark stats', error);
        this.bookmarksCount = 0;
        this.savedCount = 0;
      }
    });
  }

  passwordMatchValidator(form: FormGroup) {
    const newPassword = form.get('newPassword');
    const confirmPassword = form.get('confirmPassword');
    
    if (newPassword && confirmPassword && newPassword.value !== confirmPassword.value) {
      confirmPassword.setErrors({ passwordMismatch: true });
      return { passwordMismatch: true };
    }
    return null;
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('File size must be less than 5MB');
        return;
      }

      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
      }

      this.uploadProfilePicture(file);
    }
  }

  uploadProfilePicture(file: File): void {
    this.authService.uploadProfilePicture(file).subscribe({
      next: (response: { pictureUrl: string }) => {
        console.log('Profile picture updated', response);
        this.successMessage = 'Profile picture updated successfully!';
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error: any) => {
        console.error('Failed to upload profile picture', error);
        alert('Failed to upload profile picture. Please try again.');
      }
    });
  }

  updateProfile(): void {
    if (this.profileForm.invalid) {
      return;
    }

    this.isSaving = true;
    this.successMessage = '';

    const updates = this.profileForm.value;

    this.authService.updateProfile(updates).subscribe({
      next: (user: User) => {
        console.log('Profile updated', user);
        this.isSaving = false;
        this.successMessage = 'Profile updated successfully!';
        this.profileForm.markAsPristine();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error: any) => {
        console.error('Failed to update profile', error);
        this.isSaving = false;
        alert('Failed to update profile. Please try again.');
      }
    });
  }

  changePassword(): void {
    if (this.passwordForm.invalid) {
      return;
    }

    this.isChangingPassword = true;

    const { currentPassword, newPassword } = this.passwordForm.value;

    // Call API to change password
    // For now, just simulate the call
    setTimeout(() => {
      this.isChangingPassword = false;
      this.passwordForm.reset();
      this.successMessage = 'Password changed successfully!';
      setTimeout(() => this.successMessage = '', 3000);
    }, 1500);
  }

  resetForm(): void {
    this.profileForm.patchValue({
      name: this.user?.name,
      email: this.user?.email,
      phone: this.user?.phone || '',
      location: this.user?.location || '',
      bio: this.user?.bio || ''
    });
    this.profileForm.markAsPristine();
  }

  deleteAccount(): void {
    const confirmed = confirm(
      'Are you sure you want to delete your account? This action cannot be undone.'
    );

    if (confirmed) {
      const doubleConfirmed = confirm(
        'This will permanently delete all your data. Are you absolutely sure?'
      );

      if (doubleConfirmed) {
        // Call API to delete account
        console.log('Deleting account...');
        this.authService.logout();
        this.router.navigate(['/']);
      }
    }
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
