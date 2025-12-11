import { Component } from '@angular/core';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { DemarchesSimplifieesService } from '../../services/demarches-simplifiees.service';
import { FileData } from './interfaces';

@Component({
  selector: 'app-depobio',
  templateUrl: './depobio.component.html',
  styleUrls: ['./depobio.component.css'],
})
export class DepobioComponent {
  fileNumber: string = '';
  message: string = '';
  isError: boolean = false;
  isLoading: boolean = false;
  fileData: FileData | null = null;
  currentUser: User;

  constructor(
    private demarcheSimplifieeService: DemarchesSimplifieesService,
    private _authService: AuthService
  ) {}

  isValidInteger(value: string) {
    if (!value) return false;
    const number = Number(value);
    // Condition pour être un nombre sur graphql
    return Number.isInteger(number) && number >= -2147483648 && number <= 2147483647;
  }

  getFile() {
    if (!this.fileNumber) {
      return;
    }

    this.message = '';
    this.isError = false;
    this.isLoading = true;
    this.fileData = null;
    this.demarcheSimplifieeService.getFile(this.fileNumber).subscribe({
      next: (data) => {
        this.fileData = data;
        this.message = 'Le dossier a été trouvé dans Démarches Simplifiées.';
        this.isError = false;
        this.isLoading = false;
      },
      error: (error) => {
        if ((error.status === 404 || error.status === 403) && error.error?.description) {
          this.message = error.error?.description;
        } else {
          this.message = 'Une erreur est survenue lors de la vérification du dossier.';
        }
        this.isError = true;
        this.isLoading = false;
        this.fileData = null;
      },
    });
  }

  createAF() {
    const currentUser = this._authService.getCurrentUser();
    try {
      const apiUrl = this.demarcheSimplifieeService.createAFUrl(this.fileData, currentUser);
      window.location.href = apiUrl; // Redirige dans le même onglet
    } catch (error) {
      this.isError = true;
      this.message = "Erreur lors de la génération de l'URL : " + error.error?.description;
    }
  }
}
