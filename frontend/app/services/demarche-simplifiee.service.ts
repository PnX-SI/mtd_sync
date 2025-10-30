import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from '@geonature/services/config.service';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DemarcheSimplifieeService {
  constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {}

  verifierDossier(numeroDossier: string): Observable<any> {
    const apiUrl = `${this.config.API_ENDPOINT}/${this.config.PLUGIN_DEPOBIO.MODULE_URL}/validate_folder_number/${numeroDossier}`;
    return this.http.get<any>(apiUrl);
  }
}