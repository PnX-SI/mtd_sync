import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {ConfigService} from '@geonature/services/config.service';
import {Observable} from 'rxjs';
import {ModuleService} from '@geonature/services/module.service';

@Injectable({
    providedIn: 'root'
})
export class DemarcheSimplifieeService {
    constructor(
        private http: HttpClient,
        private config: ConfigService,
        private module: ModuleService
    ) {
    }

    getFolder(folderNumber: string): Observable<any> {
        const apiUrl = `${this.config.API_ENDPOINT}/${this.config.PLUGIN_DEPOBIO.MODULE_URL}/get_folder/${folderNumber}`;
        return this.http.get<any>(apiUrl);
    }

    createAFUrl(folderData: any): string {
        const params = new URLSearchParams({
            id: folderData.id,
            libelle: folderData.libelle,
            description: folderData.description || '',
            number: folderData.number,
            state: folderData.state,
            date_fin: folderData.date_fin || ''
        });
        return `${this.config.URL_APPLICATION}/#/${this.module.getModule("METADATA").module_url}/af?${params.toString()}`;
    }

}