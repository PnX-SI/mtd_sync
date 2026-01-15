import { Component } from '@angular/core';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { ConfigService } from '@geonature/services/config.service';
import { ModuleService } from '@geonature/services/module.service';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
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
  isDescriptionVisible: boolean = false;
  isError: boolean = false;
  isLoading: boolean = false;
  fileData: FileData | null = null;
  currentUser: User;
  existingAfUrls: string[] = [];

  constructor(
    private demarcheSimplifieeService: DemarchesSimplifieesService,
    private _authService: AuthService,
    private config: ConfigService,
    private module: ModuleService
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
    this.existingAfUrls = [];

    forkJoin({
      file: this.demarcheSimplifieeService.getFile(this.fileNumber),
      afIds: this.demarcheSimplifieeService
        .getAfFromFileNumber(this.fileNumber)
        .pipe(catchError(() => of(null))),
    }).subscribe({
      next: (res) => {
        this.fileData = res.file;
        const existingAfIds = res.afIds as number[]
        this.isLoading = false;
        if (existingAfIds && existingAfIds.length > 0) {
          this.existingAfUrls = existingAfIds.map((id) =>
            this.demarcheSimplifieeService.getExistingAfUrl(id)
          );
          this.message =
            existingAfIds.length > 1
              ? 'Le dossier a été trouvé et plusieurs cadres d’acquisition existent déjà.'
              : 'Le dossier a été trouvé et un cadre d’acquisition existe déjà.';
        } else {
          this.message = 'Le dossier a été trouvé dans Démarches Simplifiées.';
        }
        this.isError = false;
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
