import { Component } from '@angular/core';
import {DemarcheSimplifieeService} from "../../services/demarche-simplifiee.service";

@Component({
  selector: 'app-depobio',
  templateUrl: './depobio.component.html',
  styleUrls: ['./depobio.component.css']
})
export class DepobioComponent {
  numeroDossier: string = '';
  message: string = '';
  isError: boolean = false;
  isLoading: boolean = false;

  constructor(private demarcheSimplifieeService: DemarcheSimplifieeService) {}

  verifierDossier() {
    if (!this.numeroDossier) {
      return;
    }

    this.message = '';
    this.isError = false;
    this.isLoading = true;

    this.demarcheSimplifieeService.verifierDossier(this.numeroDossier).subscribe({
      next: () => {
        this.message = 'Le dossier existe dans démarche simplifiée.';
        this.isError = false;
        this.isLoading = false;
      },
      error: (error) => {
        this.message = error.status === 404
          ? 'Le dossier n\'existe pas dans démarche simplifiée.'
          : 'Une erreur est survenue lors de la vérification du dossier.';
        this.isError = true;
        this.isLoading = false;
      }
    });
  }
}
