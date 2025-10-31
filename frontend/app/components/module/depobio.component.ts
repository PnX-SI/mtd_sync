import {Component} from '@angular/core';
import {DemarcheSimplifieeService} from "../../services/demarche-simplifiee.service";

@Component({
    selector: 'app-depobio',
    templateUrl: './depobio.component.html',
    styleUrls: ['./depobio.component.css']
})
export class DepobioComponent {
    folderNumber: string = '';
    message: string = '';
    isError: boolean = false;
    isLoading: boolean = false;
    folderData: any = null;

    constructor(private demarcheSimplifieeService: DemarcheSimplifieeService) {
    }

    getFolder() {
        if (!this.folderNumber) {
            return;
        }

        this.message = '';
        this.isError = false;
        this.isLoading = true;
        this.folderData = null;
        this.demarcheSimplifieeService.getFolder(this.folderNumber).subscribe({
            next: (data) => {
                this.folderData = data
                this.message = 'Le dossier a été trouvé dans démarches simplifiées.';
                this.isError = false;
                this.isLoading = false;
            },
            error: (error) => {
                this.message = error.status === 404
                    ? 'Le dossier n\'existe pas dans démarches simplifiées.'
                    : 'Une erreur est survenue lors de la vérification du dossier.';
                this.isError = true;
                this.isLoading = false;
                this.folderData = null;
            }
        });
    }

    createAF() {
        try {
            const apiUrl = this.demarcheSimplifieeService.createAFUrl(this.folderData);
            window.location.href = apiUrl; // Redirige dans le même onglet
        } catch (error) {
            console.error('Erreur lors de la génération de l\'URL:', error);
        }
    }

}
