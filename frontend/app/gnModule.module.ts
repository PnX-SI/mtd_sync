import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { RouterModule, Routes } from '@angular/router';
import { DepobioComponent } from './components/depobio/depobio.component';

const routes: Routes = [{ path: '', component: DepobioComponent }];

@NgModule({
  declarations: [DepobioComponent],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    MatListModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatProgressSpinnerModule,
  ],
  exports: [],
  providers: [],
  bootstrap: [DepobioComponent],
})
export class GeonatureModule {}
